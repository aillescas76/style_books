import requests
import json
import os
import time

import openai
from dotenv import load_dotenv

load_dotenv(".env")
client = openai.OpenAI()

 
def download_png_image(name, url):
     """
     Downloads a PNG image from a URL and saves it with a given name.
     
     :param name: Name of the file to save the image as (without extension).
     :param url: URL of the image to download.
     """
     try:
         # Send a GET request to the URL
         response = requests.get(url, stream=True)
 
         # Check if the request was successful
         if response.status_code == 200:
             # Open a file with the given name for writing in binary mode
             with open(f"{name}.png", 'wb') as file:
                 # Write the content of the response to the file
                 file.write(response.content)
             print(f"Image successfully downloaded and saved as '{name}.png'.")
         else:
             # Handle responses with error status codes
             print(f"Failed to download image. Status code: {response.status_code}")
     except requests.exceptions.RequestException as e:
         # Handle exceptions raised by the requests library
         print(f"An error occurred while downloading the image: {e}")

def generate_structure(base_name):
     i = 0
     img_path = f"{base_name}/img"
     if os.path.isdir(base_name):
          if os.path.isdir(img_path):
               i = len(os.listdir(img_path))
          else:
               os.mkdir(img_path)
     else:
          os.mkdir(base_name)
          os.mkdir(img_path)
     if os.path.isfile(f"{base_name}/style_book_{base_name}.json"):
          with open(f"{base_name}/style_book_{base_name}.json") as f:
               style_book = json.load(f)
     else:
          style_book = {}
     if not "urls" in style_book:
          style_book["urls"] = []
     return i, style_book

def generate_style(initial_prompt: str, base_name:str, num_iterations: int=50):
     i, style_book = generate_structure(base_name)
     end_iteration = i + num_iterations
     while i < end_iteration:
         print("Generation", i)
         try:
             result = client.images.generate(model="dall-e-3", prompt=initial_prompt)
         except KeyError:
              print("User exit request")
              return
         except:
             print("Bad request")
             continue
         current_name = f"{base_name}/img/{base_name}_{i:0>{len(str(num_iterations))}}"
         image = result.data[0]
         style_book[current_name.split("/")[-1]] = str(image.revised_prompt)
         style_book["urls"].append(image.url)
         with open(f"{base_name}/style_book_{base_name}.json", "w") as style_book_file:
             style_book_file.write(json.dumps(style_book))
         download_png_image(current_name, image.url)
         time.sleep(1)
         i += 1

def generate_markdown(directory_path, output_filename='README.md'):
     """
     Generate a markdown document with images and their descriptions.
 
     :param directory_path: Path to the directory containing image files.
     :param output_filename: The filename for the generated markdown document.
     """
     # Initialize the markdown content
     markdown_content = "# Image Gallery\n\n"
     descriptor_file = [filename for filename in os.listdir(directory_path) if filename.startswith("style_book")]
     if not descriptor_file:
          print(f"Not valid descriptor file in {directory_path}")
          return
     descriptor_file = descriptor_file[0]
     file_descriptions = json.load(open(descriptor_file, "r"))
     directory_path = os.path.join(directory_path, "img")
     # Add images and descriptions to markdown content
     files = os.listdir(directory_path)
     files.sort()
     for filename in files:
         file_path = os.path.join(directory_path, filename)
         # Check if the current file is a file and not a directory
         if os.path.isfile(file_path):
             # Include only files that have a description in the dictionary
             filedescriptor = filename.split(".")[0]
             if filedescriptor in file_descriptions:
                 # Generate image markdown string
                 image_markdown = f"![{file_descriptions[filedescriptor]}]({file_path})"
                 markdown_content += image_markdown + "\n\n"
                 markdown_content += f"*{file_descriptions[filedescriptor]}*\n\n"
 
     # Write the markdown content to the output file
     with open(output_filename, 'w') as markdown_file:
         markdown_file.write(markdown_content)