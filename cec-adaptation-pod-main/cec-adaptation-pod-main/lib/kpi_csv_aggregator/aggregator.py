import logging
import re
from collections import OrderedDict
from enum import Enum
from typing import List, NamedTuple, Tuple, Optional


class Oper(Enum):
    sum = 1
    avg = 2
    tps = 3
    ready = 999


class CntType(Enum):
    KPI = 1
    Cnt = 2


KpiDef = NamedTuple('KpiDef', name=str, matches=frozenset, operation=Oper, counter_type=CntType)
KpiAndValue = NamedTuple("KpiAndValue", name=str, value=Optional[float])


def fs(list) -> frozenset:
    return frozenset(list)


class Aggregator:
    def __init__(self, interval_mins: int):
        self.interval_mins = interval_mins
        self.interval_value_avg = int(self.interval_mins / 5)
        self.values_by_kpi: OrderedDict[KpiDef, List[str]] = OrderedDict()

    def reg_cnt(self, kpi_def: KpiDef) -> KpiDef:
        self.values_by_kpi[kpi_def] = []
        return kpi_def

    @staticmethod
    def match(kpi_def: KpiDef, line: str) -> bool:
        for pattern in kpi_def.matches:
            compiled_pattern = re.compile(pattern)
            if 'TEST' in kpi_def.name and compiled_pattern.search(line):
                print(f'pattern = {pattern}, line = {line}')
            if not compiled_pattern.search(line):
                return False
        return True

    @staticmethod
    def kpi_value_from_line(line: str) -> Tuple[str, str]:
        kpi_name = ""
        kpi_value = 0
        fields = line.split(",")
        for field in fields:
            if "countername" in field:
                key_value = field.split("=")
                kpi_name = key_value[1] if len(key_value) == 2 else ""

            if "countervalue" in field:
                key_value = field.split("=")
                kpi_value = key_value[1].strip() if len(key_value) == 2 else ""

        return kpi_name, kpi_value

    def kpi_add_value(self, kpi_def: KpiDef, line: str) -> bool:
        if not kpi_def in self.values_by_kpi:
            self.values_by_kpi[kpi_def] = []

        if not self.match(kpi_def, line):
            return False

        kpi_name, value = self.kpi_value_from_line(line)
        values = self.values_by_kpi.get(kpi_def, [])
        values.append(value)
        self.values_by_kpi[kpi_def] = values
        return True

    @staticmethod
    def format_kpi_value(value: float) -> Optional[str]:
        if not value:
            return None
        elif type(value) == int or value.is_integer():
            return '{0:.0f}'.format(value)
        else:
            return '{0:.2f}'.format(round(value, 2))

    def log_kpi(self, kpi_name: str, counter_type: CntType, value: float, values: List[str], op_name: str, matches: []):
        logging.info(
            f"{counter_type.name}: {kpi_name} = {self.format_kpi_value(value)} <-- ({op_name} {', '.join(values)}) <== {list(matches)}")

    def log_kpi_def(self, kpi_def: KpiDef, value: float):
        values = self.values_by_kpi[kpi_def]
        self.log_kpi(kpi_def.name, kpi_def.counter_type, value, values, kpi_def.operation.name, kpi_def.matches)

    def aggregate_counters(self, filepath: str):
        with open(filepath, 'r') as f:
            for line in f.readlines():
                for kpi_def in self.values_by_kpi.keys():
                    self.kpi_add_value(kpi_def, line)

    def calc_simple_kpi(self, kpi_def: KpiDef) -> Optional[float]:
        values: List[str] = self.values_by_kpi[kpi_def]

        if len(values) == 0:
            return 0

        if kpi_def.operation == Oper.sum:
            total = sum(map(float, values))
        elif kpi_def.operation == Oper.avg:
            total = sum(map(float, values)) / self.interval_value_avg
        elif kpi_def.operation == Oper.tps:
            total = sum(map(float, values)) / (self.interval_mins * 60)
        elif kpi_def.operation == Oper.ready:
            total = values[0]
        else:
            raise ValueError(f'Operation "{kpi_def.operation}" not implemented')

        self.log_kpi_def(kpi_def, total)

        return total

    def sum_counters(self, kpi_defs: List[KpiDef]) -> float:
        total = 0

        for kpi_def in kpi_defs:
            # values: List[str] = self.values_by_kpi[kpi_def]
            total += self.calc_simple_kpi(kpi_def)
            # total += sum(map(float, values))
        return total

    @staticmethod
    def success_rate(success: Optional[float], total: Optional[float]) -> Optional[float]:
        if not total:
            return None

        if total == 0:
            return 0

        if success == 0:
            return 0

        if not success:
            return 0

        return success / total * 100

    def rate_kpi(self, kpi_name: str, portion: KpiDef, total: KpiDef) -> KpiAndValue:
        value: Optional[float] = self.success_rate(self.calc_simple_kpi(portion), self.calc_simple_kpi(total))
        self.log_kpi(kpi_name, CntType.KPI, value, [], f'{portion.name} / {total.name}', frozenset())
        return KpiAndValue(kpi_name, value)
