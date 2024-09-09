import requests
import time
from colorama import Fore, Style, init
import sys
import io

# Set encoding terminal ke UTF-8 untuk mengatasi masalah karakter Unicode
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

init(autoreset=True)

# API URLs
url_register = "https://api-tg-app.midas.app/api/auth/register"
url_user = "https://api-tg-app.midas.app/api/user"
url_game = "https://api-tg-app.midas.app/api/game/play"
url_referral = "https://api-tg-app.midas.app/api/referral/status"
url_referral_claim = "https://api-tg-app.midas.app/api/referral/claim"

user_agent = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"

def read_init_data(file_path):
    # Read initData from the specified file
    with open(file_path, 'r') as file:
        init_data = [line.strip() for line in file.readlines()]
    return init_data

def get_auth_token(init_data):
    # Register and get the authorization token using initData
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "id,en-US;q=0.9,en;q=0.8",
        "content-type": "application/json",
        "priority": "u=1, i",
        "sec-ch-ua": "\"Not)A;Brand\";v=\"99\", \"Google Chrome\";v=\"127\", \"Chromium\";v=\"127\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "Referer": "https://midas-tg-app.netlify.app/",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "User-Agent": user_agent
    }

    body = {
        "initData": init_data
    }

    try:
        response = requests.post(url_register, headers=headers, json=body, timeout=10)
        response.raise_for_status()

        # Respons tidak dalam bentuk JSON, ambil teks langsung
        token = response.text
        if token:  # Pastikan token tidak kosong
            print(f"Berhasil mendapatkan token: {token[:20]}...")  # Cetak sebagian token untuk verifikasi
            return token
        else:
            print(f"{Fore.RED}Token tidak ditemukan dalam respons.{Style.RESET_ALL}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request error while fetching auth token: {e}")
        return None

def get_request(url, headers):
    # Perform a GET request with error handling
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None

def post_request(url, headers):
    # Perform a POST request with error handling
    try:
        response = requests.post(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None

def claim_referral_rewards(headers, retries=3):
    # Try to claim referral rewards up to a specified number of retries
    for attempt in range(retries):
        referral_data = get_request(url_referral, headers)
        
        if referral_data:
            can_claim = referral_data.get("canClaim", False)
            
            if can_claim:
                print(f"{Fore.GREEN}Klaim tersedia! Mengeksekusi klaim...{Style.RESET_ALL}")
                claim_response = post_request(url_referral_claim, headers)
                
                if claim_response:
                    total_points = claim_response.get("totalPoints", 0)
                    total_tickets = claim_response.get("totalTickets", 0)
                    print(f"Klaim berhasil! Anda mendapatkan {total_points} poin dan {total_tickets} tiket.")
                    return total_points, total_tickets
                else:
                    print(f"{Fore.RED}Error saat mengeksekusi klaim.{Style.RESET_ALL}")
                    return 0, 0
            else:
                print(f"{Fore.YELLOW}Tidak ada klaim yang tersedia saat ini.{Style.RESET_ALL}")
                return 0, 0
        else:
            print(f"{Fore.RED}Request error. Mencoba kembali... ({attempt+1}/{retries}){Style.RESET_ALL}")
            time.sleep(5)
            
    print("Gagal mengakses API referral setelah beberapa percobaan.")
    return 0, 0

def get_user_info(headers):
    # Fetch and display user information
    data = get_request(url_user, headers)
    if data:
        telegram_id = data.get("telegramId", "Tidak ditemukan")
        username = data.get("username", "Tidak ditemukan")
        first_name = data.get("firstName", "Tidak ditemukan")
        points = data.get("points", "Tidak ditemukan")
        tickets = data.get("tickets", 0)
        games_played = data.get("gamesPlayed", "Tidak ditemukan")
        streak_days_count = data.get("streakDaysCount", "Tidak ditemukan")

        # Handle Unicode characters in output
        first_name_clean = first_name.encode('ascii', 'ignore').decode('ascii')

        print(f"Telegram ID: {telegram_id}")
        print(f"Username: {Fore.CYAN}{username}{Style.RESET_ALL}")
        print(f"First Name: {first_name_clean}")  # Print with clean first name
        print(f"Points: {points}")
        print(f"Tickets: {tickets}")
        print(f"Games Played: {games_played}")
        print(f"Streak Days Count: {streak_days_count}")
        
        return points, tickets
    else:
        print("Error: Tidak dapat mengakses API user.")
        return 0, 0

def play_game(headers):
    # Play the game and collect points
    total_points = 0
    taps = 9

    for i in range(taps):
        print(f"Memulai tap {i+1}...")
        game_data = post_request(url_game, headers)
        if game_data:
            points_earned = game_data.get("points", 0)
            total_points += points_earned
            
            print(f"Tap {i+1}: Earned {points_earned} points, Total Points: {total_points}")
            
            if total_points >= 16:
                print("Game selesai! Total poin telah mencapai 16.")
                break
        else:
            print(f"{Fore.RED}Error saat memainkan game.{Style.RESET_ALL}")
            break
        
        time.sleep(1)
    
    if total_points < 16:
        print(f"Game selesai! Anda telah melakukan {taps} tap, tetapi hanya mendapatkan {total_points} poin.")

if __name__ == "__main__":
    while True:  # Loop to repeat every 60 minutes
        init_data_list = read_init_data('auth.txt')
        total_points_sum = 0
        
        for init_data in init_data_list:
            print(f"\n{Fore.YELLOW}{'-'*50}{Style.RESET_ALL}")
            print(f"Memproses initData: ...{init_data[:10]}...")
            token = get_auth_token(init_data)
            if not token:
                print(f"{Fore.RED}Gagal mendapatkan token otorisasi.{Style.RESET_ALL}")
                continue

            headers = {
                "Authorization": f"Bearer {token}",
                "User-Agent": user_agent
            }

            print("Memeriksa klaim referral...")
            claimed_points, claimed_tickets = claim_referral_rewards(headers)
            claimed_tickets_used = False

            if claimed_tickets > 0:
                print(f"Tiket dari klaim referral: {claimed_tickets}")
            else:
                print(f"Tidak ada tiket yang diperoleh dari klaim referral.")

            while True:
                print("Mendapatkan informasi user...")
                points, tickets = get_user_info(headers)
                total_points_sum += points
                
                if tickets == 0 and claimed_tickets > 0 and not claimed_tickets_used:
                    tickets += claimed_tickets
                    claimed_tickets_used = True
                
                if tickets > 0:
                    print(f"\nTiket tersedia: {tickets}. Bermain game dengan 9 tap...")
                    play_game(headers)
                    tickets -= 1
                    claimed_tickets = 0
                    time.sleep(2)
                else:
                    print("Tiket habis. Tidak bisa bermain lagi.")
                    break

        print(f"{Fore.GREEN}Total points dari semua user: {total_points_sum}{Style.RESET_ALL}")

        # Wait 60 minutes before repeating
        print(f"{Fore.YELLOW}Menunggu 60 menit sebelum eksekusi ulang...{Style.RESET_ALL}")
        time.sleep(3600)
