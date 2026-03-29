def scrape_job_description(url):
    import requests
    from bs4 import BeautifulSoup

    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")

        text = soup.get_text(separator=" ")

        if not text or len(text.strip()) == 0:
            return ""

        return text[:3000]

    except Exception as e:
        return ""