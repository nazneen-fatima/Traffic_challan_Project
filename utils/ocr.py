

# import os
# import base64

# from dotenv import load_dotenv
# from groq import Groq


# # ============================================================
# # LOAD ENVIRONMENT VARIABLES
# # ============================================================

# load_dotenv()

# GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# if not GROQ_API_KEY:
#     raise ValueError("GROQ_API_KEY is not found in .env")


# # ============================================================
# # GROQ CLIENT
# # ============================================================

# client = Groq(
#     api_key=GROQ_API_KEY
# )


# # ============================================================
# # READ NUMBER PLATE
# # ============================================================

# def read_plate(plate_image_path):

#     # --------------------------------------------------------
#     # READ CROPPED NUMBER PLATE IMAGE
#     # --------------------------------------------------------

#     with open(plate_image_path, "rb") as image_file:

#         image_base64 = base64.b64encode(
#             image_file.read()
#         ).decode("utf-8")


#     # --------------------------------------------------------
#     # SEND IMAGE TO GROQ VISION MODEL
#     # --------------------------------------------------------

#     response = client.chat.completions.create(

#         model="qwen/qwen3.8-27b",

#         messages=[
#             {
#                 "role": "user",

#                 "content": [

#                     {
#                         "type": "text",

#                         "text": (
#                             "This image contains a cropped vehicle "
#                             "number plate. Read the vehicle "
#                             "registration number carefully. "
#                             "Return ONLY the registration number. "
#                             "Do not provide any explanation."
#                         )
#                     },

#                     {
#                         "type": "image_url",

#                         "image_url": {
#                             "url": (
#                                 f"data:image/jpeg;base64,"
#                                 f"{image_base64}"
#                             )
#                         }
#                     }

#                 ]
#             }
#         ],

#         temperature=0
#     )


#     # --------------------------------------------------------
#     # GET OCR RESULT
#     # --------------------------------------------------------

#     plate_number = (
#         response
#         .choices[0]
#         .message
#         .content
#         .strip()
#     )

#     return plate_number



import os
import base64

from dotenv import load_dotenv
from groq import Groq


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not found in .env")


# ============================================================
# GROQ CLIENT
# ============================================================

client = Groq(
    api_key=GROQ_API_KEY
)


# ============================================================
# READ NUMBER PLATE
# ============================================================

def read_plate(plate_image_path):

    # --------------------------------------------------------
    # READ CROPPED NUMBER PLATE IMAGE
    # --------------------------------------------------------

    with open(plate_image_path, "rb") as image_file:

        image_base64 = base64.b64encode(
            image_file.read()
        ).decode("utf-8")


    # --------------------------------------------------------
    # SEND IMAGE TO GROQ VISION MODEL
    # --------------------------------------------------------

    response = client.chat.completions.create(

        model="qwen/qwen3.8-27b",

        messages=[
            {
                "role": "user",

                "content": [

                    {
                        "type": "text",

                        "text": (
                            "This image contains a cropped vehicle "
                            "number plate. Read the vehicle "
                            "registration number carefully. "
                            "Return ONLY the registration number. "
                            "Do not provide any explanation."
                        )
                    },

                    {
                        "type": "image_url",

                        "image_url": {
                            "url": (
                                f"data:image/jpeg;base64,"
                                f"{image_base64}"
                            )
                        }
                    }

                ]
            }
        ],

        temperature=0,

        # Keep the response very short because
        # we only need the vehicle registration number.
        max_tokens=100
    )


    # --------------------------------------------------------
    # GET OCR RESULT
    # --------------------------------------------------------

    plate_number = (
        response
        .choices[0]
        .message
        .content
        .strip()
    )

    return plate_number

