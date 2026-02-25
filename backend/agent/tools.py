TOOLS = [
    {
        "name": "update_script",
        "description": (
            "Save the final agreed video script. Call this once the user is happy "
            "with the script content."
        ),
        "input_schema": {
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
    {
        "name": "generate_image",
        "description": (
            "Generate a single image via the image generation API. "
            "Call once per image needed."
        ),
        "input_schema": {
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
    {
        "name": "generate_video",
        "description": (
            "Submit the video generation job using the script and generated images. "
            "This is async — it returns once the video is fully rendered."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "script": {
                    "type": "string",
                    "description": "The video script to use as the generation prompt.",
                },
                "duration": {
                    "type": "integer",
                    "enum": [5, 10],
                    "description": "Video duration in seconds.",
                },
            },
            "required": ["script", "duration"],
        },
    },
    {
        "name": "update_pipeline_step",
        "description": "Advance the pipeline to the next step.",
        "input_schema": {
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
]
