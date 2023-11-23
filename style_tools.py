import asyncio
import json
import os
import time
from typing import Tuple
from openai.types import ImagesResponse

import requests
import openai
from dotenv import load_dotenv

load_dotenv(".env")
client = openai.AsyncOpenAI()

 
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


async def generate_image(order: int, prompt: str) -> Tuple[int, openai.types.ImagesResponse]:
     print("Generating image", order)
     image = await client.images.generate(model="dall-e-3", prompt=prompt)
     print("Generated image", order)
     return (order, image)

async def generate_images(num_iterations: int, prompt: str):
     result = await asyncio.gather(*[generate_image(order, prompt) for order in range(num_iterations)])
     return result

def generate_style(initial_prompt: str, base_name:str, num_iterations: int=50):
     i, style_book = generate_structure(base_name)
     data = []
     try:
          data = asyncio.run(generate_images(num_iterations, initial_prompt))
     except KeyError:
          print("User exit request")
     except Exception as e:
          print("Bad request", e)
     for (order, image_response) in data:
          order = order + i
          current_name = f"{base_name}/img/{base_name}_{order:0>{len(str(num_iterations))}}"
          image = image_response.data[0]
          style_book[current_name.split("/")[-1]] = str(image.revised_prompt)
          style_book["urls"].append(image.url)
          with open(f"{base_name}/style_book_{base_name}.json", "w") as style_book_file:
               style_book_file.write(json.dumps(style_book))
               download_png_image(current_name, image.url)


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
     files.sort(key=lambda f: int(f.split('.')[0].split('_')[-1]))
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


def story_crafter(promt:str):
     client = openai.AsyncOpenAI()
     writer = agents["writer"]


# Define sub-functions for clarity and code organization
def send_to_openai(prompt, message, model="gpt-4-1106-preview", conversation="conversation.json") -> str:
    """Send a message to OpenAI with the specified prompt."""
    # Assume OpenAI has a f<unction named `openai.ChatCompletion.create` for sending messages
    response = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": message}
        ]
    )
    add_to_conversation(conversation, response)
    return str(response.choices[0].message.content)

def add_to_conversation(conversation_file_name, gpt_response):
     if os.path.isfile(conversation_file_name):
          with open(conversation_file_name, "r") as f:
               conversation = json.load(f)
     else:
          conversation = []

     conversation.append(gpt_response.json)
     with open(conversation_file_name, "w") as f:
          f.write(json.dumps(conversation))

def illustrate_character(characters, system_prompts) -> str:
    """Send characters to OpenAI with the illustrator_character system prompt."""
    return send_to_openai(system_prompts['illustrator_character'], characters)

def illustrate_scene(characters, chapter_text, system_prompts) -> str:
    """Send characters and chapter text to OpenAI with the illustrator_scene system prompt."""
    scene_prompt = f"{characters}\n\n{chapter_text}"
    return send_to_openai(system_prompts['illustrator_scene'], scene_prompt)

# Main function to handle the conversation flow
def craft_story(user_prompt):
    """Handle the conversation flow as per the specified steps."""
    with open("prompts.json", "r") as prompts_file:
         system_prompts = json.load(prompts_file)
    # Step 1: Send initial user prompt to the "writer"
    writer_response = send_to_openai(system_prompts['writer'], user_prompt)

    # Step 2: Send writer's response to the "critic"
    critic_response = send_to_openai(system_prompts['critic'], writer_response)
    review_prompt = "Rewrite the following story schema: '''{}'''  with this criticism: '''{}'''"

    # Step 3: Send critic's response back to the "writer"
    writer_followup_response = send_to_openai(
         system_prompts['writer'], 
         review_prompt.format(writer_response, critic_response),
    )

    # Step 4: Send the follow-up writer's response to the "editor"
    editor_response = send_to_openai(system_prompts['editor'], writer_followup_response)
    storys_data = json.loads(editor_response[7:-3])
    # From the editor's response, extract characters and handle the chapter illustration
    characters = storys_data["characters"]
    story_context = storys_data["summary"]

    characters_prompt = f"This is the list of characters: {characters} and a bit of context of the story: {story_context}"
    # Step 5: Send characters to the "illustrator_character"
    character_illustrations = illustrate_character(characters_prompt, system_prompts)
    character_illustrations = character_illustrations[7:-3] 
    # Step 6: For each chapter, send a request to OpenAI with the characters and the chapter text
    # Extract chapters from the editor's response. Assuming chapters are separated by some delimiter
    chapters = storys_data["chapters"]  # Replace with actual delimiter in the response
    scene_illustrations = []
    for chapter in chapters:
        scene_illustrations.append(illustrate_scene(characters, chapter, system_prompts))

    # Return the illustration results
    return character_illustrations, scene_illustrations
