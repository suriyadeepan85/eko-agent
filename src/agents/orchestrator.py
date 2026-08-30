"""
Orchestrator - main agent pipeline coordinator.
"""

import logging
from .. import retrieval
from ..run_record import RunRecord
from . import planner, pooling, reasoner, validator, memory

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def run_pipeline(question: str, project_root: str = ".") -> 'RunRecord':
    """Execute full agent pipeline.

    Args:
        question: User question
        project_root: Project root for run records

    Returns:
        RunRecord with complete trace and final answer
    """
    record = RunRecord(question, project_root)

    # Step 1: Plan
    context = memory.get_context()
    plan_result = planner.plan(question, context)
    record.add_plan(plan_result['decomposed'], plan_result['sub_questions'])

    # Step 2: Retrieve
    sub_questions = plan_result['sub_questions']
    if not plan_result['decomposed']:
        sub_questions = [question]

    retrievals = []
    for sub_q in sub_questions:
        chunks = retrieval.query(sub_q, k=5)
        retrievals.append((sub_q, chunks))
        record.add_retrieval(sub_q, 5, None, chunks)

    # Check for insufficient retrieval
    total_chunks = sum(len(chunks) for _, chunks in retrievals)
    if total_chunks == 0:
        record.add_failure('insufficient_retrieval')
        record.set_answer("No relevant documents found for this question.")
        record.print_summary()
        record.flush()
        return record

    # Step 3: Pool
    pooled = pooling.pool_chunks(retrievals)
    doc_ids = [c['doc_id'] for c in pooled]
    record.add_pooled_chunks(doc_ids)

    # Step 4: Reason + Validate loop (max 2 attempts)
    prior_attempt = None
    rejection_reasons = []

    for attempt_num in range(1, 3):  # attempts 1 and 2
        try:
            # Reason
            reason_result = reasoner.reason(question, pooled, context, prior_attempt)

            # Validate
            val_result = validator.validate(
                reason_result['draft'],
                reason_result['claims'],
                pooled
            )

            # Record attempt
            record.add_attempt(
                attempt_num,
                reason_result['draft'],
                reason_result['claims'],
                val_result['verdict'],
                val_result.get('reason')
            )

            # Record precedence
            for prec in reason_result.get('precedence', []):
                record.add_precedence(
                    prec['rule'],
                    prec['winner'],
                    prec['over']
                )

            # Check verdict
            if val_result['verdict'] == 'accepted':
                # Success!
                record.set_answer(reason_result['draft'])
                cited_docs = list(set(
                    doc_id
                    for claim in reason_result['claims']
                    for doc_id in claim['doc_ids']
                ))
                record.add_sources(cited_docs)
                record.print_summary()
                record.flush()
                return record

            # Rejected - prepare for retry
            rejection_reasons.append(val_result['reason'])
            prior_attempt = {
                'draft': reason_result['draft'],
                'reason': val_result['reason']
            }

        except Exception as e:
            logging.error(f"Attempt {attempt_num} failed: {e}")
            record.add_failure('invalid_input', {'error': str(e)})
            if attempt_num == 2:
                break

    # Retry exhausted
    if len(rejection_reasons) == 2 and rejection_reasons[0] == rejection_reasons[1]:
        record.add_failure('repeated_rejection', {
            'reason': rejection_reasons[0]
        })

    record.add_failure('retry_exhausted', {
        'attempts': 2,
        'reasons': rejection_reasons
    })

    # Build informative refusal
    refusal = f"""I cannot provide a grounded answer to this question.

Searched for: {', '.join(sub_questions)}
Retrieved documents: {', '.join(doc_ids)}

The retrieved documents do not contain sufficient information to answer your question with confidence."""

    record.set_answer(refusal)
    record.print_summary()
    record.flush()

    return record
