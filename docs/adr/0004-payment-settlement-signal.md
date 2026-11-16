# ADR-0004: Settlement signal for receivables/payables — matched payments, not `amount_residual`

## Status

Accepted (2026-11-16). Corrects the "known platform issue" recorded in `docs/roadmap.md` on 2026-08-09.

## Context

On 2026-08-09 the Epic 02 prototype recorded that `account.payment.register` created payments
without a journal entry (`move_id = False`), that `action_post` on `account.payment` failed with
`TypeError: cannot marshal None`, and attributed both to trial infrastructure. Re-examined on
2026-11-16 against `saas~19.4+e`:

1. **No journal entry is by design, not a bug.** Since Odoo 18, a bank journal whose payment
   method lines have no *outstanding account* (`account.payment.method.line.payment_account_id`)
   registers payments without an accounting entry. The invoice is flagged `in_payment` through
   `account.move.matched_payment_ids`; its accounting `amount_residual` stays at the full amount
   until a bank statement line is reconciled. On `benacta.odoo.com` all four payment method lines
   of journal `BNK1` have `payment_account_id = False`, and no bank statement is ever imported, so
   every one of the 38 payments has `move_id = False` and every invoice keeps its full residual.
2. **`cannot marshal None` is XML-RPC, not Odoo.** `action_post` returns `None`, which XML-RPC
   cannot serialise. The call itself succeeds. Use JSON-RPC or ignore the return value.

Consequence before this ADR: `working_capital.py` treated `amount_residual > 0` as "outstanding",
so every invoice ever issued appeared open and AR aging / DSO were meaningless.

## Decision

- The ERP Adapter derives the business-level settlement of each document from its matched
  payments: `Move.amount_paid`, `Move.effective_residual`, `Move.last_payment_date`,
  `Move.is_settled`. Only payments in state `in_process` or `paid` count. If Odoo *has*
  reconciled a payment (accounting residual already below total), the accounting residual wins
  so nothing is counted twice. The raw `amount_residual` stays on the Move for traceability.
- Every analytic that reasons about what is owed uses `effective_residual`, never
  `amount_residual` or the `payment_state` label.
- Time-dependent analytics default to the synthetic enterprise's business clock
  (`DATASET_AS_OF = 2026-08-09`, exported by the adapter) and accept an explicit `as_of`.
- We do **not** configure outstanding accounts on the bank journal for now. It would only affect
  payments registered after the change, and it would change the accounting shape of the dataset
  (extra entries on 511xxx accounts) without changing the business facts. It stays an option if
  a storyline needs bank reconciliation (cash position, unapplied cash).

## Consequences

- AR/AP aging, working capital and DSO are now computable: on the dataset clock, settled
  documents drop out of the aging and partial payments age only for their remainder.
- One extra batched `account.payment` read per invoice query (ids from `matched_payment_ids`).
- If outstanding accounts are configured later, the adapter needs no change: the
  accounting-residual branch takes over automatically.
- `docs/roadmap.md` "Known platform issue" is superseded by this ADR.
