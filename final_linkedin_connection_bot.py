import time
import random
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException, NoSuchElementException

# Set up Chrome options to keep the browser open after script execution
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)

# Function to scroll the page to load more connection recommendations
def scroll_page(driver):
    number_of_scrolls = 0
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        # Scroll down to the bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        number_of_scrolls += 1

        # Calculate new scroll height and compare with the last height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if (new_height == last_height) or (number_of_scrolls >= 5):
            break  # If the height hasn't changed, we've reached the end of the page
        last_height = new_height

# Function to navigate to profile and check number of connections
def check_profile_connections(driver):
    # Navigate to the LinkedIn connections page
    driver.get('https://www.linkedin.com/mynetwork/invite-connect/connections/')
    time.sleep(5)
    
    try:
        # Find and extract the number of connections from the header
        connections_text = driver.find_element(By.XPATH, "//header[@class='mn-connections__header']//h1").text
        
        # Extract just the number of connections (e.g., "162")
        connections_count = int(connections_text.split()[0].replace('+', '').replace(',', ''))
        print(f"Current number of connections: {connections_count}")

        # Check if the limit of 30,000 is reached
        if connections_count >= 30000:
            print("We have reached the maximum limit of 30,000 connections.")
            return True
    except NoSuchElementException:
        print("Could not find the connections element on the profile page.")
    except ValueError:
        print("Error in extracting the number of connections.")
    return False

# Function to close pop-ups or overlays
def close_popups(driver):
    try:
        close_button = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Dismiss')]")
        close_button.click()
        time.sleep(1)
    except NoSuchElementException:
        pass

# Function to send connection requests from "My Network"
def send_network_connections(driver, day, connections_sent_per_day, total_connections_limit):
    remaining_connections = total_connections_limit - sum(connections_sent_per_day)

    # For the first 6 days, pick a random number of connections between 5 and 10
    if day < 6:
        connection_limit = min(random.randint(10, 14), remaining_connections)
    else:
        # On the 7th day, send the exact number of remaining connections to reach 100
        connection_limit = remaining_connections
        print(f"Day {day + 1}: Sending remaining {connection_limit} connections to reach 100.")

    if connection_limit <= 0:
        print(f"Day {day + 1}: No connections left to send.")
        return

    # Scroll the page to load more recommendations
    scroll_page(driver)

    # Find all the 'Connect' buttons
    connect_buttons = driver.find_elements(By.XPATH, "//span[text()='Connect']/ancestor::button")

    connections_sent_today = 0

    for button in connect_buttons:
        if connections_sent_today >= connection_limit:
            break

        try:
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", button)
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(button))
            time.sleep(1)
            button.click()  # Click the Connect button
            time.sleep(2)

            # Confirm the connection request (if a pop-up appears)
            try:
                send_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Send')]")
                send_button.click()  # Click 'Send' if the confirmation pop-up appears
                time.sleep(2)  # Pause to ensure the request is sent
            except NoSuchElementException:
                print("No confirmation required, request sent.")

            connections_sent_today += 1  # Increment the counter

        except ElementClickInterceptedException:
            print("Click intercepted, trying to close pop-ups or scroll.")
            close_popups(driver)  # Try to close any blocking pop-ups
            continue  # Retry after handling pop-ups        

        except TimeoutException:
            print("Element was not clickable in time, moving to next.")
            continue  # Skip if the button doesn't become clickable in time

        except Exception as e:
            print(f"Error sending connection request: {e}")
            continue

    # Store the number of connections sent today in the array
    connections_sent_per_day[day] = connections_sent_today
    print(f"Day {day + 1}: Successfully sent {connections_sent_today} connection requests.")

# Function to search for people by job role
def search_by_job_role(driver, job_role):
    # Access the LinkedIn search bar and enter the job role
    search_box = driver.find_element(By.XPATH, "//input[contains(@aria-label, 'Search')]")
    search_box.clear()
    search_box.send_keys(job_role)
    search_box.send_keys(Keys.RETURN)
    
    # Wait for the search results to load
    time.sleep(5)

    # Navigate to the "People" tab in search results
    try:
        people_tab = driver.find_element(By.XPATH, "//button[contains(@class, 'search-reusables__filter-pill-button') and contains(text(), 'People')]")
        people_tab.click()
        time.sleep(3)
    except NoSuchElementException:
        print("Could not find the 'People' button.")

def run_weekly_script():
    # Initialize WebDriver
    ''' To download chromedriver version automatically remove hash from the below two lines and put an hash in front of third line below this'''
    #service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
    #driver = webdriver.Chrome(service=service, options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()

    # Open LinkedIn login page
    driver.get('https://www.linkedin.com/login')

    # Find the username and password fields and enter your login credentials
    try:
        username = driver.find_element(By.ID, 'username')
        password = driver.find_element(By.ID, 'password')
    except NoSuchElementException:
        print("Login page elements not found.")
        driver.quit()

    # Enter your LinkedIn credentials
    username.send_keys('e-mail')
    password.send_keys('password')

    # Submit the login form
    password.send_keys(Keys.RETURN)

    # Wait for a while to ensure the page has loaded
    time.sleep(5)
    
    # Check the number of connections on your profile before sending more connections
    if check_profile_connections(driver):
        print("No more connections will be sent as the maximum limit is reached.")
        return  # Exit the script if the maximum connection limit is reached

    # Open the "My Network" page on LinkedIn
    driver.get('https://www.linkedin.com/mynetwork/')
    time.sleep(5)

    # Loop to run the script every 7 days (weekly)
    while True:
        # Reset the connections sent array and the total weekly limit at the start of each week
        connections_sent_per_day = [0] * 7  # Array for 7 days
        total_connections_limit = 100

        # Run the script once a day for 7 days
        for day in range(7):
            job_roles = ['student', 'faculty']
            for role in job_roles:
                print(f"Searching for {role}s...")
                search_by_job_role(driver, role)
                send_network_connections(driver, day, connections_sent_per_day, total_connections_limit)
            if sum(connections_sent_per_day) >= total_connections_limit:
                print("Weekly connection limit of 100 reached.")
                break  # Stop if the total number of connections has reached the weekly limit

            # Wait until midnight for the next day
            now = datetime.now()
            midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            time_to_sleep = (midnight - now).total_seconds()
            print(f"Sleeping until next day ({midnight})...")
            time.sleep(time_to_sleep)

        # Reset for the next week after 7 days
        print("Resetting the script for the next week...")
        time.sleep(1)  # Small pause before resetting for the next week

    # Quit the driver after sending connections
    driver.quit()

# Run the weekly script
run_weekly_script()
