import os
import tkinter as tk
from tkinter import filedialog, Label, Frame, Entry
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
from PIL import Image
from pathlib import Path
import logging
from colorama import Fore, Style
from typing import Tuple

logger = logging.Logger("tk watermark logger", level=logging.DEBUG)


def select_file():
    filename = filedialog.askopenfilename(filetypes=[("MP4 files", "*.mp4")])
    video_path_entry.delete(0, tk.END)
    video_path_entry.insert(0, str(Path(filename)))


def select_watermark():
    filename = filedialog.askopenfilename(filetypes=[("Png files", "*.png")])
    watermark_path_entry.delete(0, tk.END)
    watermark_path_entry.insert(0, str(Path(filename)))


def select_output():
    output_dir = filedialog.askdirectory()
    output_path_entry.delete(0, tk.END)
    output_path_entry.insert(0, str(Path(output_dir)))


def change_filename(file_path: Path, characters: str):
    stem = file_path.stem
    ext = file_path.suffix
    output_filename = Path(stem + characters + ext)
    return output_filename


def convert_watermark(watermark_str_path: str):
    p = Path(watermark_str_path)
    p_out = p.parent.joinpath(Path("watermark_rgba.png"))
    watermark = Image.open(p).convert("RGBA")
    watermark.save(p_out)

    return str(p_out)


def render():
    status_label["text"] = "Rendering"
    video_path = video_path_entry.get()
    logo_path = convert_watermark(watermark_path_entry.get())
    position = position_dict[var.get()]

    output_name = output_name_entry.get()

    if output_name.endswith(".mp4"):
        output_path = Path(output_path_entry.get()).joinpath(Path(output_name))
    else:
        status_label["text"] = "extension must be mp4"
        return

    if not output_name:  # empty output name
        output_path = change_filename(output_path, "watermarked")

    logger.debug(
        f"video_path: {video_path} \noutput_path: {output_path}\nlogo_path: {logo_path}\nposition: {position}"
    )

    assert video_path and output_path and logo_path and position

    def set_logo_size(videoclip: VideoFileClip, size: Tuple[int, int] = None, factor_width=None, factor_height=None):
        if factor_width:
            return {'width': int(videoclip.size[0] * factor_width)}

        if factor_height:
            return {'height': int(videoclip.size[1] * factor_height)}

        raise ValueError("Use percent_width or percent height or a size tuple pair")

    video = VideoFileClip(video_path)
    logo = (
        ImageClip(logo_path, transparent=True)
        .set_duration(video.duration)
        .resize(**set_logo_size(video, factor_width=0.1))  # TODO expose width height to ui
        .set_pos(position)  # TODO expose margin to ui
    )

    final = CompositeVideoClip([video, logo], size=video.size)

    try:
        final.write_videofile(str(output_path), threads=os.cpu_count())
    except ValueError as e:
        print(Fore.RED + "=" * 10)
        print("RENDER FAILED")
        print(
            "Some program might optimize white or black image to grayscale automatically"
        )
        print("Make sure the watermark file is in srgb colorspace, NOT grayscale")
        print("=" * 10)
        print(Style.RESET_ALL)
        raise e

    status_label["text"] = f"Wrote: {str(output_path)}"


position_key = [
    "Top_Left",
    "Top",
    "Top_Right",
    "Center_Left",
    "Center",
    "Center_Right",
    "Bottom_Left",
    "Bottom",
    "Bottom_Right",
]

position_val = [
    ("left", "top"),
    ("center", "top"),
    ("right", "top"),
    ("left", "center"),
    ("center", "center"),
    ("right", "center"),
    ("left", "bottom"),
    ("center", "bottom"),
    ("right", "bottom"),
]

position_dict = {key: val for key, val in zip(position_key, position_val)}

# make gui
root = tk.Tk()

# top
top_frame = Frame()
title = Label(master=top_frame, text="Tk watermarker")
title.pack()
var = tk.StringVar(value="Center")  # default position
top_frame.pack()

# mid
middle_frame = Frame()
for i, position in enumerate(position_dict.items()):
    k, v = position
    rb = tk.Radiobutton(master=middle_frame, text=k, variable=var, value=k)
    rb.grid(row=i // 3, column=i % 3)
middle_frame.pack()

# bottom
bottom_frame = Frame()

select_video_button = tk.Button(
    master=bottom_frame, text="Select file", command=select_file
)
select_watermark_button = tk.Button(
    bottom_frame, text="Select watermark file", command=select_watermark
)
select_output_button = tk.Button(
    master=bottom_frame, text="Set output path", command=select_output
)

output_name_label = tk.Label(master=bottom_frame, text="filename")
status_label = tk.Label(master=bottom_frame, text="")

video_path_entry = Entry(master=bottom_frame, width=50)
watermark_path_entry = Entry(master=bottom_frame, width=50)
output_path_entry = Entry(master=bottom_frame, width=50)
output_name_entry = Entry(master=bottom_frame, width=50)
render_button = tk.Button(bottom_frame, text="Render", command=render)

video_path_entry.grid(row=0, column=0, columnspan=2)
select_video_button.grid(row=0, column=2, columnspan=1)

watermark_path_entry.grid(row=1, column=0, columnspan=2)
select_watermark_button.grid(row=1, column=2, columnspan=1)

output_path_entry.grid(row=2, column=0, columnspan=2)
select_output_button.grid(row=2, column=2, columnspan=1)

output_name_label.grid(row=3, column=0, columnspan=1)
output_name_entry.grid(row=3, column=1, columnspan=1)

status_label.grid(row=4, column=0, columnspan=1)
render_button.grid(row=4, column=2, columnspan=1)
bottom_frame.pack()

DEBUG_MODE = False
if DEBUG_MODE:
    video_path_entry.insert(0, "C:\\Users\\K\\Videos\\Airline Cm Rc2-1.mp4")
    watermark_path_entry.insert(0, "C:\\Users\\K\\Videos\\watermark_white.png")
    output_path_entry.insert(0, "C:\\Users\\K\\Videos")
    output_name_entry.insert(0, "tt.mp4")

root.mainloop()
