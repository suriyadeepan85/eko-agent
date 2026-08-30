import json
import os
import re
import logging
from datetime import datetime


class RunRecord:
    """Write-only audit trail for a single question.

    Incrementally builds a complete record of retrieval, reasoning,
    and validation events. Flushes to JSON file in /runs/ directory.
    """

    def __init__(self, question: str, project_root: str = "."):
        """Initialize record with question and timestamp.

        Creates filename: {timestamp}_{question-slug}.json
        Ensures /runs/ directory exists.
        """
        self.question = question
        self.timestamp = datetime.utcnow().isoformat() + 'Z'
        self.project_root = project_root

        self.record = {
            'question': question,
            'timestamp': self.timestamp,
            'plan': {},
            'retrievals': [],
            'pooled_chunks': [],
            'attempts': [],
            'precedence_applied': [],
            'answer': None,
            'sources': [],
            'failures': []
        }

        slug = self._slugify(question)
        ts_safe = self.timestamp.replace(':', '-')
        self.filename = f"{ts_safe}_{slug}.json"

        self.runs_dir = os.path.join(project_root, 'runs')
        os.makedirs(self.runs_dir, exist_ok=True)
        self.filepath = os.path.join(self.runs_dir, self.filename)

    def add_plan(self, decomposed: bool, sub_questions: list[str] = None):
        """Record query decomposition plan."""
        self.record['plan'] = {
            'decomposed': decomposed,
            'sub_questions': sub_questions or []
        }

    def add_retrieval(self, sub_question: str, k: int,
                      filters: dict | None, chunks: list[dict]):
        """Record retrieval results for a sub-question.

        Args:
            chunks: From retrieval.query() - will strip 'text' field
        """
        filtered_chunks = [
            {
                'doc_id': c['doc_id'],
                'score': c['score'],
                'effective_date': c.get('effective_date'),
                'authority_tier': c.get('authority_tier')
            }
            for c in chunks
        ]

        self.record['retrievals'].append({
            'sub_question': sub_question,
            'k': k,
            'filters': filters,
            'chunks': filtered_chunks
        })

    def add_pooled_chunks(self, doc_ids: list[str]):
        """Record deduplicated doc IDs across all retrievals."""
        self.record['pooled_chunks'] = doc_ids

    def add_attempt(self, attempt_num: int, draft: str,
                    claims: list[dict], verdict: str, reason: str = None):
        """Record reasoning attempt with grounding claims.

        Args:
            claims: List of {'claim': str, 'doc_id': str} pairs
            verdict: 'accepted' or 'rejected'
            reason: Rejection reason if verdict='rejected'
        """
        self.record['attempts'].append({
            'attempt': attempt_num,
            'draft': draft,
            'claims': claims,
            'verdict': verdict,
            'reason': reason
        })

    def add_precedence(self, rule: str, winner: str, over: str):
        """Record precedence rule application.

        Example: rule='later_effective_date', winner='D4', over='C3'
        """
        self.record['precedence_applied'].append({
            'rule': rule,
            'winner': winner,
            'over': over
        })

    def set_answer(self, answer: str):
        """Set final answer."""
        self.record['answer'] = answer

    def add_sources(self, doc_ids: list[str]):
        """Record documents cited in final answer."""
        self.record['sources'] = doc_ids

    def add_failure(self, failure_type: str, details: dict = None):
        """Record failure condition.

        Types: insufficient_retrieval, weak_retrieval, filtered_empty,
               low_grounding, conflicting_output, retry_exhausted,
               repeated_rejection, invalid_input
        """
        failure = {'type': failure_type}
        if details:
            failure['details'] = details
        self.record['failures'].append(failure)

    def flush(self):
        """Write record to JSON file."""
        with open(self.filepath, 'w') as f:
            json.dump(self.record, f, indent=2)
        logging.info(f"Run record written to {self.filepath}")

    def to_dict(self) -> dict:
        """Return the complete record as a dictionary.

        Returns:
            Copy of the internal record dict with all trace data
        """
        return self.record.copy()

    @property
    def answer(self) -> str:
        """Get the final answer."""
        return self.record['answer']

    def print_summary(self):
        """Print human-readable summary to console."""
        print(f"\n{'=' * 60}")
        print(f"QUESTION: {self.record['question']}")
        print(f"TIMESTAMP: {self.record['timestamp']}")
        print('=' * 60)

        if self.record['plan']:
            if self.record['plan']['decomposed']:
                print(f"\nPLAN: Decomposed into {len(self.record['plan']['sub_questions'])} sub-questions")
                for sq in self.record['plan']['sub_questions']:
                    print(f"  - {sq}")
            else:
                print("\nPLAN: Direct query (no decomposition)")

        print(f"\nRETRIEVALS: {len(self.record['retrievals'])} queries")
        for r in self.record['retrievals']:
            print(f"  Sub-question: {r['sub_question']}")
            print(f"  Chunks: {len(r['chunks'])} (k={r['k']})")
            for chunk in r['chunks'][:3]:
                print(f"    - {chunk['doc_id']} (score: {chunk['score']:.4f})")
            if len(r['chunks']) > 3:
                print(f"    ... and {len(r['chunks']) - 3} more")

        print(f"\nATTEMPTS: {len(self.record['attempts'])} reasoning attempts")
        for att in self.record['attempts']:
            verdict_mark = '✓' if att['verdict'] == 'accepted' else '✗'
            print(f"  Attempt {att['attempt']}: {verdict_mark} {att['verdict']}")
            if att['reason']:
                print(f"    Reason: {att['reason']}")

        if self.record['precedence_applied']:
            print(f"\nPRECEDENCE: {len(self.record['precedence_applied'])} rules applied")
            for prec in self.record['precedence_applied']:
                print(f"  {prec['winner']} won over {prec['over']} via {prec['rule']}")

        if self.record['answer']:
            print(f"\nANSWER: {self.record['answer'][:200]}")
            if len(self.record['answer']) > 200:
                print("  ...")
        else:
            print("\nANSWER: (no answer generated)")

        if self.record['sources']:
            print(f"\nSOURCES: {len(self.record['sources'])} documents")
            for doc_id in self.record['sources']:
                print(f"  - {doc_id}")

        if self.record['failures']:
            print(f"\nFAILURES: {len(self.record['failures'])}")
            for fail in self.record['failures']:
                print(f"  - {fail['type']}")
                if 'details' in fail:
                    print(f"    {fail['details']}")

        print('=' * 60 + '\n')

    def _slugify(self, text: str, max_len: int = 60) -> str:
        """Convert text to filesystem-safe slug."""
        slug = text.lower()[:max_len]
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = slug.strip('-')
        return slug
