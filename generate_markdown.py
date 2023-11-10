import os

def generate_markdown(directory_path, file_descriptions, output_filename='README.md'):
     """
     Generate a markdown document with images and their descriptions.
 
     :param directory_path: Path to the directory containing image files.
     :param file_descriptions: A dictionary {filename: description} for the image files.
     :param output_filename: The filename for the generated markdown document.
     """
     # Initialize the markdown content
     markdown_content = "# Image Gallery\n\n"
 
     # Add images and descriptions to markdown content
     for filename in os.listdir(directory_path):
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
