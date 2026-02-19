from profile import Profile

def main():
    """
    Docstring for main
    """
    google_client_id = input("Enter your Google Client ID: ") 
    google_client_secret = input("Enter your Google Client Secret: ") 
    print("Invalid login. Please try again. ")
    google_client_id = input("Enter your Google Client ID: ") 
    google_client_secret = input("Enter your Google Client Secret: ") 
    print("You have been successfully logged in!")
    print("Welcome to weightTrack! Please add your profile.")
    new_profile = Profile()
    new_profile.name = input("What is your name? ")
    new_profile.weight = input("What is your weight (in lbs)? ")
    new_profile.age = input("What is your age? ")
    new_profile.gender = input("What is your gender? ")
    new_profile.activity_level = input("What is your activity level per week? ")
    new_profile.goals = input("What is your weight goal? ")
    print("The amount of calories you need to eat per day for the next 2 months to get to weight 175 is 1950.")
    input("Calories eaten 7 days ago: ")
    input("Calories eaten 6 days ago: ")
    input("Calories eaten 5 days ago: ")
    input("Calories eaten 4 days ago: ")
    input("Calories eaten 3 days ago: ")
    input("Calories eaten 2 days ago: ")
    input("Calories eaten 1 day ago: ")
    print("Recommended macros: 50 grams of protein, 200 grams of carbohydrates, 25 grams of fiber, 66 grams of sugar, 58 grams of fat, and 19 grams of saturated fat.")
    input("Want to logout? (y or n) ")
    print("You have been successfully logged out!")

if __name__ == "__main__":
    main()
    
