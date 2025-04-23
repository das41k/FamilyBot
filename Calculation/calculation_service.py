import math
from typing import Union, Dict, List, Optional
from datetime import datetime, timedelta

class FinanceCalculator:
    """
    Основной класс для финансовых расчетов.
    Содержит методы для кредитов, вкладов, накоплений и бюджета.
    """

    # ----------------- Кредитный калькулятор -----------------
    @staticmethod
    def calculate_loan(
            amount: float,
            annual_rate: float,
            months: int,
            loan_type: str = "annuity"  # "annuity" или "diff"
    ) -> dict:
        monthly_rate = annual_rate / 12 / 100

        if loan_type == "annuity":
            # Аннуитетный расчет
            payment = amount * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)
            return {
                "monthly_payment": round(payment, 2),
                "total_payment": round(payment * months, 2),
                "overpayment": round(payment * months - amount, 2),
                "payment_type": "annuity"
            }
        else:
            # Дифференцированный расчет
            base_payment = amount / months
            payments = []
            remaining = amount

            for month in range(1, months + 1):
                # Уменьшаем остаток ПЕРЕД расчетом платежа
                if month > 1:
                    remaining -= base_payment
                    remaining = max(remaining, 0)  # Защита от отрицательных значений

                interest = remaining * monthly_rate
                total_payment = base_payment + interest

                # Корректировка для последнего месяца
                if month == months:
                    total_payment = remaining + interest
                    base_payment = remaining

                payments.append({
                    "month": month,
                    "payment": round(total_payment, 2),
                    "principal": round(base_payment, 2),
                    "interest": round(interest, 2),
                    "remaining": round(remaining - base_payment, 2) if month < months else 0.00
                })

            # Принудительно обнуляем остаток в последнем месяце
            payments[-1]["remaining"] = 0.00

            return {
                "first_payment": round(payments[0]['payment'], 2),
                "last_payment": round(payments[-1]['payment'], 2),
                "total_payment": round(sum(p['payment'] for p in payments), 2),
                "overpayment": round(sum(p['interest'] for p in payments), 2),
                "payment_type": "differentiated",
                "schedule": payments
            }

    # ----------------- Калькулятор вкладов -----------------
    @staticmethod
    def _calculate_deposit_interest(
            amount: float,
            annual_rate: float,
            months: int,
            deposit_type: str = "capitalization"
    ) -> tuple[float, float, list[dict]]:
        """
        Общая логика для расчёта вклада. Возвращает:
        - итоговую сумму
        - общие проценты
        - график платежей
        """
        monthly_rate = annual_rate / 12 / 100
        schedule = []
        total = amount
        total_interest = 0.0

        for month in range(1, months + 1):
            if deposit_type == "capitalization":
                interest = total * monthly_rate
                total += interest
            else:
                interest = amount * monthly_rate

            total_interest += interest
            schedule.append({
                "month": month,
                "interest": round(interest, 2),
                "end_amount": round(total, 2) if deposit_type == "capitalization" else round(amount + total_interest, 2)
            })

        return round(total, 2), round(total_interest, 2), schedule

    @staticmethod
    def calculate_deposit(
            amount: float,
            annual_rate: float,
            months: int,
            deposit_type: str = "capitalization"
    ) -> dict:
        """
        Возвращает только итоговые значения для вклада.
        Используется, когда график платежей не нужен.
        """
        total, interest, _ = FinanceCalculator._calculate_deposit_interest(
            amount, annual_rate, months, deposit_type
        )
        if deposit_type != "capitalization":
            total = amount + interest
        return {
            "total": total,
            "interest": interest,
            "type": deposit_type
        }

    @staticmethod
    def generate_deposit_schedule(
            amount: float,
            annual_rate: float,
            months: int,
            deposit_type: str = "capitalization"
    ) -> list[dict]:
        """
        Генерирует подробный график платежей по вкладу.
        Используется для отображения помесячной статистики.
        """
        _, _, schedule = FinanceCalculator._calculate_deposit_interest(
            amount, annual_rate, months, deposit_type
        )
        return schedule

    # ----------------- Накопительный калькулятор -----------------
    @staticmethod
    def calculate_savings_comparison(
            initial: float,
            monthly_add: float,
            annual_rate: float,
            months: int,
    ) -> Dict:
        """Возвращает результаты для обоих типов начисления"""

        def calculate(capitalization: bool):
            monthly_rate = annual_rate / 12 / 100
            total = initial
            total_interest = 0
            total_added = initial
            schedule = []

            for month in range(1, months + 1):

                if capitalization:
                    interest = total * monthly_rate
                else:
                    interest = total_added * monthly_rate

                total_interest += interest
                if capitalization:
                    total += interest

                total += monthly_add
                total_added += monthly_add

                schedule.append({
                    'month': month,
                    'added': monthly_add,
                    'interest': round(interest, 2),
                    'total': round(total, 2)
                })

            return {
                "total": round(total, 2),
                "total_interest": round(total_interest, 2),
                'schedule': schedule
            }

        return {
            "with_cap": calculate(True),
            "without_cap": calculate(False)
        }

    # ----------------- Вспомогательные методы -----------------
    @staticmethod
    def validate_input(value: str, value_type: type = float) -> Optional[float]:
        """
        Проверка введенных данных.

        :param value: Введенное значение
        :param value_type: Ожидаемый тип (float/int)
        :return: Число или None при ошибке
        """
        try:
            return value_type(value)
        except ValueError:
            return None