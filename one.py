import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import requests
import time
import telebot

# Telegram Bot Token and Chat ID
BOT_TOKEN = "7869138028:AAGCULiK2P_ejEp_gv7pF-MvfzgTvnGfH4c"
CHAT_ID = "1092360448"

# Initialize the Telegram bot
bot = telebot.TeleBot(BOT_TOKEN)

# List to store questions and answers for verification
question_data = []

# Function to fetch BTC price from Binance API
def fetch_btc_open_price():
    try:
        response = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")
        response.raise_for_status()
        data = response.json()
        return float(data['price'])  # Return BTC price as a float
    except Exception as e:
        print(f"Error fetching BTC price: {e}")
        bot.send_message(CHAT_ID, f"Error fetching BTC price: {e}")
        return None

# Function to send Telegram notifications
def send_telegram_notification():
    global question_data

    # Fetch current BTC price
    btc_price = fetch_btc_open_price()
    if btc_price is None:
        return  # Exit if fetching fails

    # Example sentiment and trend analysis (replace with your logic)
    sentiment = "Bullish"  # Placeholder
    trend = "Upward"  # Placeholder

    # Determine answer based on sentiment and trend
    if sentiment == "Bullish" and trend == "Upward":
        answer = "Yes"
    elif sentiment == "Bearish" or trend == "Downward":
        answer = "No"
    else:
        answer = "Uncertain"

    # Format timestamps
    current_time = datetime.now()
    next_interval_time = current_time + timedelta(minutes=10)
    tip_time = current_time.strftime("%I:%M %p")
    question_time = next_interval_time.strftime("%I:%M %p")

    # Prepare question and answer
    question = f"Bitcoin to be priced at {btc_price:.2f} USDT or more at {question_time}?"
    tip = f"Bitcoin Open Price at {tip_time} was {btc_price:.2f} USDT.\nSentiment: {sentiment}\nTrend: {trend}"

    # Log the question and prediction for later verification
    question_data.append({
        "Question": question,
        "Prediction": answer,
        "Target Price": btc_price,
        "Target Time": next_interval_time
    })

    # Send the question, answer, and tip to Telegram
    bot.send_message(CHAT_ID, f"{question}\nAnswer: {answer}\n\n{tip}")

# Save results to an Excel file
def save_to_local_excel(results):
    df = pd.DataFrame(results)
    df.to_excel("BTC_Predictions.xlsx", index=False)
    print("Results saved to BTC_Predictions.xlsx")

# Verify predictions and save results to Excel
def verify_predictions_and_save_to_excel():
    global question_data

    results = []
    for entry in question_data:
        target_time = entry['Target Time']
        while datetime.now() < target_time:  # Wait until target time
            time.sleep(1)

        # Fetch the actual BTC price at the target time
        actual_price = fetch_btc_open_price()
        if actual_price is not None:
            # Compare the prediction
            predicted_price = entry['Target Price']
            prediction = entry['Prediction']
            is_correct = (
                (prediction == "Yes" and actual_price >= predicted_price) or
                (prediction == "No" and actual_price < predicted_price) or
                (prediction == "Uncertain")
            )

            # Log the result
            results.append({
                "Question": entry['Question'],
                "Prediction": prediction,
                "Target Time": target_time.strftime("%I:%M %p"),
                "Actual Price": actual_price,
                "Is Correct": "True" if is_correct else "False"
            })

    # Save results to Excel
    if results:
        save_to_local_excel(results)

# Scheduler Configuration
scheduler = BackgroundScheduler()

# Schedule the job to run every 10 minutes
def align_to_ten_minute_intervals():
    now = datetime.now()
    seconds_to_next_interval = (10 - now.minute % 10) * 60 - now.second
    time.sleep(seconds_to_next_interval)

align_to_ten_minute_intervals()
scheduler.add_job(send_telegram_notification, 'interval', minutes=10)
scheduler.add_job(verify_predictions_and_save_to_excel, 'interval', minutes=10)

# Start the scheduler
scheduler.start()
print("Scheduler started. Notifications will be sent every 10 minutes.")

# Keep the script running
try:
    while True:
        time.sleep(1)
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()
    print("Scheduler stopped.")
