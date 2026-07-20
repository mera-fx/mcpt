# Plain-English Strategy Explanation Standard

Every main strategy report must explain the strategy before interpreting its
results. A reader should not need to inspect Python code or infer rules from a
parameter name.

Each explanation must contain:

1. **The idea** — one short paragraph describing the market behaviour the
   strategy is attempting to exploit.
2. **The exact rules** — setup, entry, stop, exit, direction and daily limits,
   using ordinary language and stating when the signal is known and when the
   trade is executed.
3. **Parameter meanings** — what each number controls and how changing it
   changes strategy behaviour.
4. **A worked numerical example** — realistic prices showing how the setup,
   entry, risk or threshold is calculated.
5. **An important distinction** — the most likely misunderstanding, such as
   the difference between a 0.50 drive fraction and a 50% market return.

The reusable source is `strategy_explanations.py`. Current experiment and
family explanations are registered there. Shared and dedicated report
generators render that source directly, preventing wording from drifting
between reports.

For a new experiment:

- register its explanation before generating the first report;
- use completed-bar and next-bar wording explicitly where applicable;
- distinguish price percentages, standard deviations, risk multiples and
  range fractions;
- preserve positive numeric values in the normal text colour;
- use green only for favourable status words;
- use red for losses, drawdowns, failures and rejected decisions.

The `upgrade_strategy_explanations.py` utility can add the shared explanation
to already-generated HTML reports. It changes reporting files only and never
reruns a strategy, optimization, bootstrap, MCPT or lifecycle process.
