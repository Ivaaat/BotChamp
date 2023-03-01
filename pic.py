import requests
from config import User_agent
from PIL import Image, ImageEnhance
from PIL import ImageFont
from PIL import ImageDraw
from io import BytesIO
from championat import get_start_end_tour, get_next_date
import textwrap


def news_pic(logo_news, text_news):
    sess = requests.Session()
    sess.headers.update(User_agent)
    response_left_team = sess.get(logo_news)
    news_picture = Image.open(BytesIO(response_left_team.content))
    logo = Image.open(r"pic\germany.png").resize((30, 30))
    # logo = logo.resize((25,25))
    news_picture = Image.open("A.png")
    news_picture = news_picture.resize((735, 490))
    news_picture.convert("RGBA")
    enhancer = ImageEnhance.Brightness(news_picture)
    news_picture = enhancer.enhance(0.95)
    draw = ImageDraw.Draw(news_picture)
    font_size = 25
    font = ImageFont.truetype(r"ttf\gilroy-black.ttf", font_size)
    _, _, w, h = draw.textbbox((0, 0), text_news, font=font)
    i = 0
    list_text = textwrap.wrap(text_news, width=40)
    coord = (0, int(news_picture.height/2) + 50, news_picture.width,
             int(
         news_picture.height/2) + 40 + (len(list_text) + 1) * font_size)
    im_crop = news_picture.crop(coord)
    enhancer = ImageEnhance.Brightness(im_crop)
    im_crop = enhancer.enhance(0.4)
    news_picture.paste(im_crop, coord)
    news_picture.paste(logo, (0, int(news_picture.height/2) + 55 + i), logo)
    for text in list_text:
        _, _, w, h = draw.textbbox((0, 0), text, font=font)
        draw.text((35, int(news_picture.height/2 + 50 + i)), text, font=font,
                  align="center")
        i += font_size
    news_picture.paste(logo,
                       (w + 35,
                        (int(news_picture.height/2)) + 55 - font_size + i),
                       logo)
    font = ImageFont.truetype(r"ttf\\arkhip_font.ttf", 15)
    _, _, w, _ = draw.textbbox((0, 0), "Champ_footbaall", font=font)
    draw.text((news_picture.width - w - 5,
               int(news_picture.height/2 + 50 - 5 + i)),
              "Champ_footbaall", font=font, align="center")
    news_picture.show()
    return news_picture
#news_pic('https://img.championat.com/s/735x490/news/big/q/r/barselona-svyazalas-s-siti-po-povodu-arendy-huliana-alvaresa-na-sleduyuschij-sezon_16776461802145452965.jpg',
news_pic('https://img.championat.com/s/735x490/news/big/p/x/ochevidno-chto-reshenie-ne-s.jpg',
         #'| «Барселона» связалась с «Сити» по поводу аренды Хулиана Альвареса на следующий сезон |')
         '| «Очевидно, что решение не совсем справедливо». Барриос — о дисквалификациях в Кубке России «Очевидно, что решение не совсем справедливо». Барриос — о дисквалификациях в Кубке России |')


def pic_champ(name, name_champ="",
              background_pic=(), rectangle_fill=(), rgb=(0, 0, 0)):
    dict_match, name_tour, tour = get_start_end_tour(
            name, get_next_date(name))
    # img = Image.open(f"pic\{name}.png")
    # img = Image.open(f"{folder_name}\pic\\IdNH9O5FXe.jpg")
    # img.save(f'{folder_name}\pic\\football\qw1.png')
    # img = Image.open(f'{folder_name}\pic\\football\qw1.png')
    pic_player = Image.open(r"pic\football\51.png")
    pic_player = pic_player.resize((400, 700))
    rez = tour + len(dict_match)
    img = Image.new('RGBA', (1000, rez * 50 + 105), background_pic)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(r"ttf\gilroy-black.ttf", 30)
    # sadcx = font.getlength(max(tour.keys(), key=lambda i:len(i)))
    draw.polygon(xy=(
                 (1000, 0),
                 (1000, rez * 50 + 105),
                 (500 + 23, rez * 50 + 105),
                 (0, 0),
                 (0, 1000),
                 ),
                 fill='white'
                 )
    # draw.rectangle((105, 105, rez * 50 + 105, rez * 50 + 105),
    # fill="white", outline=(0, 0, 0),width=5)
    # back = Image.new('RGB',(700, 1000), rectangle_fill)
    # img.paste(back, (int(img.width/2) - int(back.width/2), 105))
    # img.paste(pic_player,(int(img.width/2) - int(pic_player.width/2),
    # int(img.height/2) - int(pic_player.height/2)),pic_player)
    logo_champ = Image.open(f"pic\\{name}.png")
    param_resize = (300, 300)
    logo_champ = logo_champ.resize(param_resize)
    # img.paste(logo_champ, (0, 0), logo_champ)
    # img.paste(logo_champ, (img.width-param_resize[0], 0), logo_champ)
    # img.paste(logo_champ, (0, img.height - param_resize[0]), logo_champ)
    # img.paste(logo_champ, (
    # img.width-param_resize[0], img.height - param_resize[0]), logo_champ)
    img.paste(logo_champ, (500, 500), logo_champ)
    label = "@Champ_footbaall"
    _, _, w, h = draw.textbbox((0, 0), label, font=font)
    pic_channel = Image.new('L', (w, h))
    ImageDraw.Draw(pic_channel).text((0, 0), label, fill=150, font=font)
    pic_channel1 = pic_channel.rotate(90, resample=Image.BICUBIC, expand=True)
    # for o in range(2):
    # img.paste((0, 0, 0),
    # (30, o * int(font.getlength(label)) + 100 + 50 * o), pic_channel1)
    # img.paste((0, 0, 0),
    # (img.width - 60, o *int(font.getlength(label)) + 100 + 50 * o),
    # pic_channel1)\
    img.paste((0, 0, 0), (30, 105), pic_channel1)
    # img.paste((0, 0, 0),
    # (img.width - 60,
    # int(img.height/2) -int(font.getlength(label)) - rez), pic_channel1)
    # img.paste((0, 0, 0), (30, int(img.height/2) + rez), pic_channel1)
    img.paste((0, 0, 0),
              (img.width - 60, img.height - int(font.getlength(label)) - 105),
              pic_channel1)
    font1 = ImageFont.truetype(r"ttf\gilroy-black.ttf", 60)
    ImageDraw.Draw(pic_channel).text((0, 0), label, fill=100, font=font1)
    # img.paste((0, 0, 0),
    # (int(img.width-font1.getlength(label)/2),
    # int(img.height-font1.getlength(label)/2)), pic_channel)
    # i = 0
    # img.paste((0, 0, 0), (int((img.width-w)/2), i), pic_channel)
    j = 5
    draw.text((int((img.width-font.getlength(name_champ)))/2, j),
              name_champ, rgb, font=font, align="center")
    j = 55
    _, _, w, _ = draw.textbbox((0, 0), name_tour, font=font)
    draw.text((int((img.width-w))/2, j), name_tour, rgb,
              font=font, align="center")
    logo_width = 50
    logo_height = 50
    shift = 5
    for date, match_url in dict_match.items():
        j += 50
        # line1 = Image.new('RGB', (1000, 5), background_pic)
        # img.paste(line1, (50, j - 9))
        _, _, w, _ = draw.textbbox((0, 0), date, font=font)
        draw.text((int((img.width-w))/2, j), date, (0, 0, 0), font=font,
                  align="center")
        e = 0
        for match_list in match_url:
            font = ImageFont.truetype(r"ttf\gilroy-black.ttf", 30)
            try:
                for match, url in match_list.items():
                    if e == 0:
                        # response_left_team = sess.get(url)
                        # logo_left_team = Image.open(BytesIO(
                        # response_left_team.content))
                        logo_left_team = Image.open(
                            f"pic\\football\\{name}\\{match}.png")
                        logo_left_team = logo_left_team.resize(
                            (logo_width, logo_height))
                        coord_x_left = int((img.width/2) - time_width)
                        _, _, w, h = draw.textbbox((0, 0), match, font=font)
                        background = Image.new('RGB', (int((img.width)/2) - 27, h + 10), 'white')
                        img.paste(background, (0, j - 5))
                        # line = Image.new('L', (700, 2))
                        # img.paste(line, (
                        # int(img.width/2) - int(line.width/2), j - 5))
                        draw.text((coord_x_left - w - shift, j), match, rgb,
                                  font=font, align = "center")
                        img.paste(logo_left_team,
                                  (coord_x_left - logo_width - w - shift,
                                   j - 5), logo_left_team )
                        e = 1
                    elif e == 1:
                        #response_right_team = sess.get(url)
                        #logo_right_team = Image.open(BytesIO(response_right_team.content))
                        logo_right_team = Image.open(f"pic\\football\{name}\{match}.png")
                        logo_right_team = logo_right_team.resize ((logo_width,logo_height))
                        coord_x_right = int((img.width/2)+time_width)
                        _, _, w, _ = draw.textbbox((0, 0), match, font=font)
                        draw.text((coord_x_right + shift, j), match , rgb, font=font, align = "center")
                        img.paste(logo_right_team, (coord_x_right + w + shift, j - 5), logo_right_team)
                        e = 0
            #except Exception as e:
            except AttributeError:
                    j += 50
                    font = ImageFont.truetype(f"ttf\gilroy-black.ttf", 25)
                    _, _, w, _ = draw.textbbox((0, 0), match_list, font=font)
                    draw.text((int((img.width-w))/2, j), match_list , rgb, font=font, align = "center")
                    time_width = w/2
    #img.paste((0, 0, 0), (int((img.width-font.getlength(label))/2), j + 50), pic_channel)
    img.save(f'pic\\football\{name}1.png')
    img.show()
    return img

# pic_champ('italy', name_champ = "Серия А, Чемпионат Италии",background_pic= (34,139,34),rectangle_fill = (144,238,144))
# pic_champ('russiapl', get_next_date('russiapl'),name_champ ="РПЛ, Чемпионат России")
# pic_champ('germany', get_next_date('germany'), name_champ = "Бундеслига, Чемпионат Германии")
# pic_champ('spain', get_next_date('spain'), name_champ="Ла Лига, Чемпионат Испании")
# pic_champ('england', get_next_date('england'), name_champ='АПЛ, Чемпионат Англии', background_pic= (199,21,133), rectangle_fill = (255,182,193))
# pic_champ('france', get_next_date('france'), name_champ="Лига 1, Чемпионат Франции")