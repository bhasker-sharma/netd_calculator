import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict

import openpyxl


@dataclass
class NETDResult:
    N: int
    mean: float
    sigma: float
    netd_mk: float
    roi_rows: int
    roi_cols: int
    frequency_table: Dict[float, int] = field(default_factory=dict)

    @property
    def roi_size(self) -> str:
        return f"{self.roi_rows} × {self.roi_cols}"


class NETDCalculator:
    """
    Computes NETD using the frequency-weighted method.

    Steps:
      1. N    = total valid temperature samples
      2. fi   = frequency of each unique temperature Ti
      3. T̄   = Σ(Ti × fi) / N
      4. σ    = sqrt(Σ[fi × (Ti − T̄)²] / N)
      5. NETD = σ × 1000  (mK)
    """

    def __init__(self, excel_path: str):
        self._excel_path = excel_path
        self._values: list = []
        self._rows: int = 0
        self._cols: int = 0

    def load_excel(self) -> None:
        wb = openpyxl.load_workbook(self._excel_path, data_only=True)
        ws = wb.active
        self._rows = ws.max_row
        self._cols = ws.max_column
        self._values = []

        for row in ws.iter_rows(values_only=True):
            for cell in row:
                if cell is None:
                    continue
                try:
                    self._values.append(float(cell))
                except (TypeError, ValueError):
                    pass  # skip empty / non-numeric cells

        if not self._values:
            raise ValueError(
                "No valid numeric temperature values found in the selected Excel file."
            )

    def calculate(self) -> NETDResult:
        if not self._values:
            raise RuntimeError("Call load_excel() before calculate().")

        N = len(self._values)

        # Step 2: frequency table
        freq: Dict[float, int] = dict(Counter(self._values))

        # Step 3: mean  T̄ = Σ(Ti × fi) / N
        mean = sum(t * f for t, f in freq.items()) / N

        # Step 4: standard deviation  σ = sqrt(Σ[fi × (Ti − T̄)²] / N)
        variance_sum = sum(f * (t - mean) ** 2 for t, f in freq.items())
        sigma = math.sqrt(variance_sum / N)

        # Step 5: NETD in mK
        netd_mk = round(sigma * 1000, 1)

        return NETDResult(
            N=N,
            mean=round(mean, 4),
            sigma=round(sigma, 6),
            netd_mk=netd_mk,
            roi_rows=self._rows,
            roi_cols=self._cols,
            frequency_table=dict(sorted(freq.items())),
        )
