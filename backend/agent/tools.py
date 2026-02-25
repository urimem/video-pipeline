TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "update_script",
            "description": (
                "Save the final agreed video script. Call this once the user is happy "
                "with the script content."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "script": {
                        "type": "string",
                        "description": "The complete video script text.",
                    }
                },
                "required": ["script"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_image",
            "description": (
                "Generate a single image via the image generation API. "
                "Call once per image needed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "image_type": {
                        "type": "string",
                        "enum": ["character", "opening", "closing"],
                        "description": "The role this image plays in the video.",
                    },
                    "prompt": {
                        "type": "string",
                        "description": "Detailed visual prompt for image generation.",
                    },
                },
                "required": ["image_type", "prompt"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_video",
            "description": (
                "Submit an image-to-video generation job. Requires a source image URL "
                "(from a previously generated image) plus a motion prompt. "
                "This is async — it returns once the video is fully rendered."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Motion/action prompt describing what happens in the video.",
                    },
                    "image_url": {
                        "type": "string",
                        "description": "URL of the source image to animate (use a previously generated image URL).",
                    },
                    "duration": {
                        "type": "integer",
                        "enum": [5, 10],
                        "description": "Video duration in seconds.",
                    },
                },
                "required": ["prompt", "image_url", "duration"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_pipeline_step",
            "description": "Advance the pipeline to the next step.",
            "parameters": {
                "type": "object",
                "properties": {
                    "step": {
                        "type": "string",
                        "enum": ["script", "images", "video", "complete"],
                        "description": "The step to transition to.",
                    }
                },
                "required": ["step"],
            },
        },
    },
]
