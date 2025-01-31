import os
from dotenv.main import load_dotenv
from langchain_openai import AzureChatOpenAI
from unstructured.partition.auto import partition
import shutil
from pdf2image import convert_from_path
import base64

load_dotenv()
os.environ["OPENAI_API_TYPE"] = "azure"


llm = AzureChatOpenAI(
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    temperature=0.8,  # print(llm.invoke("hello"))
)


def _pdf2image(path: str, user: str):

    images = convert_from_path(path)
    shutil.rmtree(f"images/{user}", ignore_errors=True)
    os.makedirs(f"images/{user}", exist_ok=True)
    for i in range(len(images)):

        images[i].save(f"images/{user}/page" + str(i) + ".png", "PNG")


# Open the image file and encode it as a base64 string
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def pdf2text(path: str, user: str):

    _pdf2image(path, user)
    image_lst = os.listdir(f"images/{user}")
    desc = ""
    for i in range(len(image_lst)):
        print("processing image", i)
        IMAGE_PATH = f"images/{user}/" + "page" + str(i) + ".png"
        base64_image = encode_image(IMAGE_PATH)

        content = [
            {
                "type": "text",
                "text": "Please extract the details of the image very  carefully  the detail should include, the date of the bill, the amount of each item along with the quantity and the total amount in case of bills if any other document then return all the details in the same format",
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{base64_image}"},
            },
        ]
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that responds in English.",
            },
            {
                "role": "user",
                "content": content,
            },
        ]

        ai_message = llm.invoke(messages)
        # print(ai_message.content)

        desc += f"\n Page {i} \n" + ai_message.content

    # print(desc)
    return desc
