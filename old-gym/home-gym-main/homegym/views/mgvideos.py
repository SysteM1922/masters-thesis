from flask import Flask




def convert_to_embed_url(url):
    video_id = url.split('v=')[1]
    embed_url = 'https://www.youtube.com/embed/' + video_id
    return embed_url


