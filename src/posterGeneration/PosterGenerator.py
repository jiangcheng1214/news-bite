import time
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import textwrap

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
}


class PosterGenerator:
    def __init__(self, canvas_width=1080, canvas_height=1080, text_font='Oswald-Regular.ttf', text_font_size=50):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.text_font = text_font
        self.text_font_size = text_font_size
        self.line_spacing = text_font_size // 5
        self.margin_size = text_font_size // 2

    def resize_image(self, image, resize_width, resize_height):
        aspect_ratio = image.size[0] / image.size[1]
        if aspect_ratio > 1:
            resize_height = int(resize_width / aspect_ratio)
        else:
            resize_width = int(resize_height * aspect_ratio)
        resized_image = image.resize((resize_width, resize_height))
        return resized_image

    def fetch_image(self, image_url, retry=0):
        try:
            response = requests.get(headers=headers, url=image_url)
            image = Image.open(BytesIO(response.content))
            return image
        except Exception as e:
            if retry < 3:
                time.sleep(5)
                return self.fetch_image(image_url, retry=retry+1)
            else:
                raise e

    def generate_instagram_poster(self, text, image_url, sentiment, post_image_path, story_image_path=None):
        # Step 1: Set up your development environment
        bull_color = (76, 175, 80)
        neutral_color = (255, 255, 255)
        bear_color = (204, 51, 0)
        whilte_color = (255, 255, 255)
        if sentiment.lower() == 'negative':
            canvas_color = bear_color
        elif sentiment.lower() == 'positive':
            canvas_color = bull_color
        else:
            canvas_color = neutral_color
        text_color = (0, 0, 0)
        canvas = Image.new(
            'RGB', (self.canvas_width, self.canvas_height), canvas_color)
        draw = ImageDraw.Draw(canvas)
        text_font = ImageFont.truetype(self.text_font, self.text_font_size)
        max_text_width = self.canvas_width
        wrapped_text = textwrap.wrap(text, width=int(
            max_text_width / self.text_font_size * 2))
        y = self.margin_size
        rectangle_start_x = self.margin_size
        rectangle_start_y = self.margin_size
        rectangle_end_x = self.canvas_width - self.margin_size
        rectangle_end_y = self.margin_size + self.text_font_size * \
            len(wrapped_text) + self.line_spacing * \
            (len(wrapped_text)-1) + self.margin_size
        draw.rectangle(
            (rectangle_start_x, rectangle_start_y, rectangle_end_x, rectangle_end_y), fill=whilte_color)
        for line in wrapped_text:
            line_width = draw.textlength(line, font=text_font)
            x = (self.canvas_width - line_width) // 2
            draw.text((x, y), line, fill=text_color, font=text_font)
            y += self.text_font_size + self.line_spacing
        y += self.text_font_size // 2 - self.line_spacing
        safe_width = self.canvas_width - self.text_font_size
        safe_height = self.canvas_height - y - self.text_font_size // 2
        post_image_generated = False
        story_image_generated = False
        try:
            image = self.fetch_image(image_url)
            resized_image = self.resize_image(image, safe_width, safe_height)
            image_width, image_height = resized_image.size
            image_position = ((self.canvas_width - image_width) //
                            2, y)
            canvas.paste(resized_image, image_position)
            poster_canvas = canvas.crop(
                (0, 0, self.canvas_width, y + image_height+self.text_font_size//2))
            poster_canvas.save(post_image_path, format='JPEG',
                            subsampling=0, quality=100)
            post_image_generated = True
        except Exception as e:
            print(f"Exception in fetching image {image_url}: {e}")
            return post_image_generated, story_image_generated

        if story_image_path:
            if not (sentiment.lower() == 'negative' or sentiment.lower() == 'positive'):
                print(
                    f"Story image is not generated for neutral sentiment {sentiment}")
            else:
                story_canvas = canvas
                story_image_draw = ImageDraw.Draw(canvas)
                text = ' BUY SIGNAL ! ' if sentiment.lower() == 'positive' else ' SELL SIGNAL ! '
                _, _, text_width, text_height = draw.textbbox(
                    (0, 0), text, font=text_font)
                canvas_width = story_canvas.size[0]
                indicator_position = (
                    (canvas_width - text_width)//2, image_position[1] + image_height//2 - text_height)
                story_image_draw.rectangle(
                    (indicator_position[0], indicator_position[1], indicator_position[0] + text_width, indicator_position[1] + text_height + self.text_font_size//3), fill=canvas_color)
                story_image_draw.text(indicator_position, text,
                                    fill=whilte_color, font=text_font)
                story_canvas = story_canvas.crop(
                    (0, 0, self.canvas_width, y + image_height+self.text_font_size//2))
                story_canvas.save(story_image_path, format='JPEG',
                                subsampling=0, quality=100)
                story_image_generated = True
        return post_image_generated, story_image_generated

if __name__ == '__main__':
    # Usage example
    generator = PosterGenerator()
    # generator.generate_poster(
    #     "Cathie Wood's ARK funds sold $26M of Coinbase stock and $13M of Tesla shares. #ARKInvestment #Coinbase #Tesla",
    #     'https://images.mktw.net/im-818918/horizontal?width=700&size=1.778975741239892&pixel_ratio=2',
    #     'neutral',
    #     'poster1.jpg',
    #     'story1.jpg')

    generator.generate_instagram_poster(
        "Bank of America is using virtual reality and artificial intelligence to train new hires. The immersive VR simulations prepare them for real-life scenarios. #BankOfAmerica #VR #AI",
        'https://thecurrencyanalytics.com/wp-content/plugins/phastpress/phast.php/c2VydmljZT1pbWFnZXMmc3JjPWh0dHBzJTNBJTJGJTJGdGhlY3VycmVuY3lhbmFseXRpY3MuY29tJTJGd3AtY29udGVudCUyRnVwbG9hZHMlMkYyMDIzJTJGMDclMkZ0MzFnMzJmdy5wbmcmY2FjaGVNYXJrZXI9MTY4OTU4NjMxOC0yODg1MDImdG9rZW49ZTExYmYxZjExYzY3Njk4Nw.q.png',
        'negative',
        'poster2.jpg',
        'story2.jpg')

    # generator.generate_poster(
    #     "The Venezuelan crypto ecosystem is still in chaos 4 months after Sunacrip's intervention. The head of Sunacrip, Joselit Ramirez, was arrested for his alleged involvement in a $20 billion corruption scandal. #Venezuela #Crypto",
    #     'https://static.news.bitcoin.com/wp-content/uploads/2023/07/shutterstock_1778799026.jpg',
    #     'positive',
    #     'poster3.jpg')
    # generator.generate_poster(
    #     'Coinbase CEO Brian Armstrong to meet with House Democrats to discuss crypto legislation. #Coinbase #crypto #legislation', 'https://crypto.snapi.dev/images/v1/g/i/fcrttom7pze6raat5wp2asst44-335009.jpg', 'Neutral', 'test.jpg')
