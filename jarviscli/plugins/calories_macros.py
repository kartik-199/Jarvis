from colorama import Fore
from plugin import plugin, alias
from typing import Callable, Tuple


class ValueOutOfRangeError(Exception):
    pass


@alias("macros")
@plugin("calories")
class CaloriesMacrosPlugin:
    """
    The current plugin calculates the recommended daily calorie intake and
    the corresponding macronutrients (proteins, carbohydrates & fats) for
    losing, maintaining or gaining weight.
    """

    class CalorieCalculator:

        WEIGHT_LOSS = 1
        WEIGHT_GAIN = 3

        def __init__(self, gender: str, age: int, height: int, weight: int,
                activity_level: int, goal: int) -> None:
            self._gender = gender
            self._age = age
            self._height = height
            self._weight = weight
            self._activity_level = activity_level
            self._goal = goal

        def _calc_rmr(self) -> float:
            """
            Resting metabolic rate (RMR) is the total number of calories burned
            when your body is completely at rest.

            The Miffin-St Jeor Equation is used to calculate the RMR as it
            is considered the most accurate when we don't know our body fat
            percentage.

            Males:   10 x weight(kg) + 6.25 x height(cm) - 5 x age(y) + 5
            Females: 10 x weight(kg) + 6.25 x height(cm) - 5 x age(y) - 161

            Sources:
                https://jandonline.org/article/S0002-8223(05)00149-5/fulltext
                https://www.medicalnewstoday.com/articles/macro-diet
            """

            WEIGHT_FACTOR = 10
            HEIGHT_FACTOR = 6.25
            AGE_FACTOR = -5
            MALE_CONSTANT = 5
            FEMALE_CONSTANT = -161

            if self._gender == 'M':
                gender_constant = MALE_CONSTANT
            else:
                gender_constant = FEMALE_CONSTANT

            return (WEIGHT_FACTOR * self._weight + HEIGHT_FACTOR * self._height
                + AGE_FACTOR * self._age + gender_constant)

        def _calc_tdee(self, rmr: float) -> int:
            """
            Total daily energy expenditure (TDEE) is the total number of
            calories someone needs to maintain his/her current weight.

            The TDEE can be estimated by multiplying the RMR by an activity
            factor. The value of that factor depends on the daily activity
            level of the individual.

            Source: https://www.medicalnewstoday.com/articles/macro-diet
            """

            ACTIVITY_FACTORS = {
                1: 1.2,    # Little or no exercise
                2: 1.375,  # Light exercise 1-3 days a week
                3: 1.55,   # Moderate exercise 4-5 days a week
                4: 1.725   # Hard exercise every day
            }

            return round(rmr * ACTIVITY_FACTORS.get(self._activity_level))

        def _calc_daily_calorie_intake(self, tdee: int) -> int:
            DAILY_CALORIC_DEFICIT = 500  # Results to ~0.5kg/week weight loss
            DAILY_CALORIC_SURPLUS = 500  # Results to ~0.5kg/week weight gain

            if self._goal == self.WEIGHT_LOSS:
                return tdee - DAILY_CALORIC_DEFICIT
            elif self._goal == self.WEIGHT_GAIN:
                return tdee + DAILY_CALORIC_SURPLUS
            else:
                return tdee

        def calc_daily_calorie_intake(self) -> int:
            rmr = self._calc_rmr()
            tdee = self._calc_tdee(rmr)
            return self._calc_daily_calorie_intake(tdee)

        def display_calorie_results(self, jarvis, cal_intake: int) -> None:
            """
            Harvard Health Publications suggests women get at least 1,200 calories
            and men get at least 1,500 calories a day unless supervised by doctors.
            """

            MIN_SUGGESTED_MALE_CAL_INTAKE = 1500
            MIN_SUGGESTED_FEMALE_CAL_INTAKE = 1200

            if self._gender == 'M' and cal_intake < MIN_SUGGESTED_MALE_CAL_INTAKE:
                jarvis.say(f'{Fore.CYAN}\nThe calculated daily calorie intake was '
                    'below the suggested of 1500 cal for males. We suggest you to '
                    'consult a nutrition expert to help you achieve your goal!')
                return

            if self._gender == 'F' and cal_intake < MIN_SUGGESTED_FEMALE_CAL_INTAKE:
                jarvis.say(f'{Fore.CYAN}\nThe calculated daily calorie intake was '
                    'below the suggested of 1200 cal for females. We suggest you '
                    'to consult a nutrition expert to help you achieve your goal!')
                return

            if self._goal == self.WEIGHT_LOSS:
                jarvis.say('\nThe recommended daily calorie intake to achieve a '
                    f'weight loss of ~0.5kg/week is: {Fore.YELLOW}{cal_intake}')
            elif self._goal == self.WEIGHT_GAIN:
                jarvis.say('\nThe recommended daily calorie intake to achieve a '
                    f'weight gain of ~0.5kg/week is: {Fore.YELLOW}{cal_intake}')
            else:
                jarvis.say('\nThe recommended daily calorie intake to maintain '
                    f'your current weight is: {Fore.YELLOW}{cal_intake}')

    def __call__(self, jarvis, _) -> None:
        self.display_welcome_message(jarvis)

        input_msg = 'Gender (M/F): '
        error_msg = 'Oops! That was not a valid gender. Please try again (M/F)...'
        gender = self.read_gender(jarvis, input_msg, error_msg)

        input_msg = 'Age: '
        bool_expression: Callable[[int], bool] = lambda age: age < 14
        error_msg = ('We suggest you to consult a nutrition expert if you are '
            'under 14 years old.'
            '\nIf you made a mistake while entering your age, try again...')
        age = self.read_input(jarvis, input_msg, bool_expression, error_msg)

        input_msg = 'Height (cm): '
        bool_expression: Callable[[int], bool] = lambda height: height <= 0
        error_msg = 'Oops! That was not a valid height. Try again...'
        height = self.read_input(jarvis, input_msg, bool_expression, error_msg)

        input_msg = 'Weight (kg): '
        bool_expression: Callable[[int], bool] = lambda weight: weight <= 0
        error_msg = 'Oops! That was not a valid weight. Try again...'
        weight = self.read_input(jarvis, input_msg, bool_expression, error_msg)

        self.display_activity_levels(jarvis)
        input_msg = 'Choose your activity level (1-4): '
        bool_expression: Callable[[int], bool] = \
            lambda activity_level: not(1 <= activity_level <= 4)
        error_msg = 'Oops! Invalid input. Try again (1-4)...'
        activity_level = self.read_input(
            jarvis, input_msg, bool_expression, error_msg)

        self.display_goals(jarvis)
        input_msg = 'Choose your goal (1-3): '
        bool_expression: Callable[[int], bool] = lambda goal: not(1 <= goal <= 3)
        error_msg = 'Oops! Invalid input. Try again (1-3)...'
        goal = self.read_input(jarvis, input_msg, bool_expression, error_msg)

        calorie_calculator = self.CalorieCalculator(
            gender, age, height, weight, activity_level, goal)
        daily_calorie_intake = calorie_calculator.calc_daily_calorie_intake()
        calorie_calculator.display_calorie_results(jarvis, daily_calorie_intake)

    def yellow(self, content: str) -> str:
        return f'{Fore.YELLOW}{content}{Fore.RESET}'

    def red(self, content: str) -> str:
        return f'{Fore.RED}{content}{Fore.RESET}'

    def display_welcome_message(self, jarvis) -> None:
        jarvis.say(self.yellow(
            '\nHello! In order to calculate your daily calorie intake '
            'i will need some information about you. Lets start...'))

    def display_activity_levels(self, jarvis) -> None:
        jarvis.say(self.yellow("\nActivity levels:"))
        jarvis.say(f'{self.yellow("[1]")} Little or no exercise')
        jarvis.say(f'{self.yellow("[2]")} Light exercise 1-3 days a week')
        jarvis.say(f'{self.yellow("[3]")} Moderate exercise 4-5 days a week')
        jarvis.say(f'{self.yellow("[4]")} Hard exercise every day\n')

    def display_goals(self, jarvis) -> None:
        jarvis.say(self.yellow("\nGoals:"))
        jarvis.say(f'{self.yellow("[1]")} Lose weight')
        jarvis.say(f'{self.yellow("[2]")} Maintain weight')
        jarvis.say(f'{self.yellow("[3]")} Gain weight\n')

    def read_gender(self, jarvis, input_message: str, error_message: str) -> str:
        while True:
            gender = jarvis.input(input_message)
            if self.validate_gender(gender):
                return gender.upper()
            print(self.red(error_message))

    def validate_gender(self, gender: str) -> bool:
        return (gender.upper() == "M" or gender.upper() == "F")

    def read_input(self, jarvis, input_message: str,
            bool_expression: Callable[[int], bool], error_message: str) -> int:
        while True:
            input = jarvis.input(input_message)
            if self.validate_input(input, bool_expression):
                return int(input)
            print(self.red(error_message))

    def validate_input(self, input: str,
            bool_expression: Callable[[int], bool]) -> bool:
        try:
            input = int(input)
            if bool_expression(input):
                raise ValueOutOfRangeError
            return True
        except (ValueError, ValueOutOfRangeError):
            return False
