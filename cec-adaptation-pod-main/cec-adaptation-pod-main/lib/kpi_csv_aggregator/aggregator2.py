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


KpiDef = NamedTuple('KpiDef', name=str, matches=frozenset, operation=Oper)
KpiAndValues = NamedTuple("KpiAndValues", kpidef=KpiDef, values=List[str])
KpiAndValue = NamedTuple("KpiAndValue", name=str, value=Optional[float])


def fs(list) -> frozenset:
    return frozenset(list)


class Aggregator2:
    def __init__(self, interval_mins: int, data_lines: List[str]):
        self.interval_mins = interval_mins
        self.data_lines = data_lines


    def agg(self, kpi_def: KpiDef) -> KpiAndValues:
        values: List[str] = []
        for line in self.data_lines:
            value = self.kpi_add_value(kpi_def, line)
            if value:
                values.append(value)
        return KpiAndValues(kpi_def, values)


    def calc_var(self, kpi_def: KpiDef) -> KpiAndValue:
        return self.calc_simple_kpi(self.agg(kpi_def), CntType.Cnt)


    def calc_kpi(self, kpi_def: KpiDef) -> KpiAndValue:
        return self.calc_simple_kpi(self.agg(kpi_def), CntType.KPI)


    def calc_simple_kpi(self, kpi_and_values: KpiAndValues, counter_type: CntType) -> KpiAndValue:
        kpi_def = kpi_and_values.kpidef
        values = kpi_and_values.values

        if len(values) == 0:
            total = None
        elif kpi_def.operation == Oper.sum:
            total = sum(map(float, values))
        elif kpi_def.operation == Oper.avg:
            total = sum(map(float, values)) / len(values)
        elif kpi_def.operation == Oper.tps:
            total = sum(map(float, values)) / (self.interval_mins * 60)
        elif kpi_def.operation == Oper.ready:
            total = values[0]
        else:
            raise ValueError(f'Operation "{kpi_def.operation}" not implemented')

        self.log_kpi_def(kpi_def, values, total, counter_type)

        return KpiAndValue(kpi_def.name, total)


    def match(self, kpi_def: KpiDef, line: str) -> bool:
        for pattern in kpi_def.matches:
            compiled_pattern = re.compile(pattern)
            if 'TEST' in kpi_def.name and compiled_pattern.search(line):
                print(f'pattern = {pattern}, line = {line}')
            if not compiled_pattern.search(line):
                return False
        return True


    def kpi_value_from_line(self, line: str) -> Tuple[str, str]:
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


    def kpi_add_value(self, kpi_def: KpiDef, line: str) -> Optional[str]:
        if not self.match(kpi_def, line):
            return None

        kpi_name, value = self.kpi_value_from_line(line)
        return value

    def format_kpi_value(self, value: float) -> Optional[str]:
        if not value:
            return None
        elif type(value) == int or value.is_integer():
            return '{0:.0f}'.format(value)
        else:
            return '{0:.2f}'.format(round(value, 2))

    def log_kpi(self, kpi_name: str, counter_type: CntType, value: float, values: List[str], op_name: str, matches: []):
        logging.info(f"{counter_type.name}: {kpi_name} = {self.format_kpi_value(value)} <-- ({op_name} {', '.join(values)}) <== {list(matches)}")

    def log_kpi_def(self, kpi_def: KpiDef, values: List[str], value: float, counter_type: CntType):
        self.log_kpi(kpi_def.name, counter_type, value, values, kpi_def.operation.name, kpi_def.matches)


    def rate(self, portion: Optional[float], total: Optional[float]) -> Optional[float]:
        if not total:
            return None

        if total == 0:
            return 0

        if not portion:
            return 0

        return portion / total * 100


    def addition_counters(self, counter_name: str, term_1: KpiAndValue, term_2: KpiAndValue, counter_type: CntType) -> KpiAndValue:
        value: Optional[float] = (term_1.value or 0) + (term_2.value or 0)
        self.log_kpi(counter_name, counter_type, value, [], f'{term_1.name} + {term_2.name}', frozenset())
        return KpiAndValue(counter_name, value)

    def rate_kpi(self, kpi_name: str, portion: KpiAndValue, total: KpiAndValue) -> KpiAndValue:
        value: Optional[float] = self.rate(portion.value, total.value)
        self.log_kpi(kpi_name, CntType.KPI, value, [], f'{portion.name} / {total.name}', frozenset())
        return KpiAndValue(kpi_name, value)

