import math
from typing import Union, Dict, List, Optional


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
    def calculate_deposit(
            amount: float,
            annual_rate: float,
            months: int,
            capitalization: bool = True
    ) -> Dict[str, float]:
        """
        Расчет доходности вклада.

        :param amount: Сумма вклада
        :param annual_rate: Годовая ставка (%)
        :param months: Срок в месяцах
        :param capitalization: Капитализация процентов
        :return: Словарь с результатами
        """
        if capitalization:
            # Заглушка для вклада с капитализацией
            return {
                "final_amount": round(amount * (1 + annual_rate / 100) ** (months / 12), 2),
                "interest": "расчет с капитализацией"
            }
        else:
            # Простой процент
            return {
                "final_amount": round(amount * (1 + annual_rate / 100 * months / 12), 2),
                "interest": "простой процент"
            }

    # ----------------- Накопительный калькулятор -----------------
    @staticmethod
    def calculate_savings(
            initial: float,
            monthly_add: float,
            annual_rate: float,
            months: int
    ) -> Dict[str, float]:
        """
        Расчет накоплений с регулярными пополнениями.

        :param initial: Начальная сумма
        :param monthly_add: Ежемесячное пополнение
        :param annual_rate: Годовая процентная ставка
        :param months: Срок в месяцах
        :return: Словарь с результатами
        """
        # Упрощенный расчет (будем дорабатывать)
        total_added = monthly_add * months
        total = initial + total_added
        return {
            "total_amount": round(total, 2),
            "total_added": round(total_added, 2),
            "interest": "расчет будет уточнен"
        }

    # ----------------- Бюджетный калькулятор -----------------
    @staticmethod
    def calculate_budget(
            income: float,
            expenses: float,
            goal: float,
            months: int
    ) -> Dict[str, float]:
        """
        Расчет бюджета для достижения финансовой цели.

        :param income: Ежемесячный доход
        :param expenses: Обязательные расходы
        :param goal: Целевая сумма
        :param months: Срок в месяцах
        :return: Словарь с рекомендациями
        """
        available = income - expenses
        monthly_saving = goal / months

        return {
            "monthly_saving": round(monthly_saving, 2),
            "possible": monthly_saving <= available,
            "daily_budget": round((available - monthly_saving) / 30, 2) if available > monthly_saving else 0
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


# Пример использования (можно удалить в рабочей версии)
if __name__ == "__main__":
    print("\nТест кредитного калькулятора (аннуитет):")
    print(FinanceCalculator.calculate_loan(1_000_000, 12, 60))

    print("\nТест вклада (с капитализацией):")
    print(FinanceCalculator.calculate_deposit(100_000, 8, 12))

    print("\nТест накоплений:")
    print(FinanceCalculator.calculate_savings(50_000, 10_000, 5, 6))

    print("\nТест бюджета:")
    print(FinanceCalculator.calculate_budget(100_000, 60_000, 240_000, 6))
