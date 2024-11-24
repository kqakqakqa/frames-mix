import os
import cv2
import numpy
import rich, rich.progress

# import ffmpeg

# input video
videoInput_path = input("输入视频: ")
if not os.path.exists(videoInput_path):
    rich.print("输入视频文件不存在!")
    exit()
videoInput = cv2.VideoCapture(videoInput_path)
# videoInputFfmpeg = ffmpeg.input(videoInput_path)
if not videoInput.isOpened():
    rich.print("无法打开视频.")
    exit()

# video info
videoInput_width = int(videoInput.get(cv2.CAP_PROP_FRAME_WIDTH))
videoInput_height = int(videoInput.get(cv2.CAP_PROP_FRAME_HEIGHT))
videoInput_fps = videoInput.get(cv2.CAP_PROP_FPS)
videoInput_frameCount = int(videoInput.get(cv2.CAP_PROP_FRAME_COUNT))
rich.print(
    f"\n[bright_yellow]{os.path.basename(videoInput_path)}",
    f"\n帧率:\t{videoInput_fps}\n帧数量:\t{videoInput_frameCount}\n",
)

# config output
videoOutput_fourcc = cv2.VideoWriter_fourcc(*"mp4v")
rich.print(f"[bright_yellow]输出")
videoOutput_fps = float(input("帧率: "))
videoOutput_frameCount = max(int(input("帧数量: ")), 1)
rich.print("")

# config process
videoProcess_shutterAngle = float(input("快门角度(%): "))
videoProcess_frameRatio = videoInput_frameCount / videoOutput_frameCount
videoProcess_mixCount = max(videoProcess_frameRatio * videoProcess_shutterAngle / 100, 1)
rich.print(f"输入 {videoProcess_mixCount} of {videoProcess_frameRatio} 帧 -> 输出 {1} 帧\n")

########

# frame_cache = {}
# videoInput_frameSize = videoInput_width * videoInput_height * 3
lastIndex = None


# def GetFrame(index, lastIndex, framesCacheMaxSize=int(min(videoProcess_mixCount, 256))):
def GetFrame(index, lastIndex):
    # if index in frame_cache:
    #     return frame_cache[index]

    # out, err = (
    #     videoInputFfmpeg.filter("select", f"gte(n,{index})")
    #     .output("pipe:", vframes=framesCacheMaxSize, format="rawvideo", pix_fmt="rgb24", vcodec="rawvideo")
    #     .run(capture_stdout=True, quiet=True)
    # )
    # frames = numpy.frombuffer(out, numpy.uint8)
    # framesCount = len(frames) / videoInput_frameSize
    # frame_chunks = numpy.split(frames, framesCount)
    # for i, frame_data in enumerate(frame_chunks):
    #     frame_cache[index + i] = frame_data.reshape((videoInput_height, videoInput_width, 3))

    if lastIndex is None or index - 1 != lastIndex:
        videoInput.set(cv2.CAP_PROP_POS_FRAMES, index)
    ret, frame = videoInput.read()
    # frame_cache[index] = frame

    ####

    # if len(frame_cache) > framesCacheMaxSize:
    #     sorted_keys = sorted(frame_cache.keys())
    #     for key in sorted_keys[:framesCacheMaxSize]:
    #         del frame_cache[key]

    return frame

videoOutput_path = (
    f"{os.path.dirname(videoInput_path)}\\{os.path.splitext(os.path.basename(videoInput_path))[0]}_帧混合_{videoOutput_fps}fps_{videoOutput_frameCount}frames_{videoProcess_shutterAngle}%.mp4"
)
videoOutput = cv2.VideoWriter(
    videoOutput_path, videoOutput_fourcc, videoOutput_fps, (videoInput_width, videoInput_height)
)

with rich.progress.Progress() as progress:
    big_task = progress.add_task("帧混合中", total=videoOutput_frameCount)
    small_task = progress.add_task("", total=0)

    for f in range(videoOutput_frameCount):
        progress.reset(small_task)
        progress.update(
            small_task,
            description=f"{int(f * videoProcess_frameRatio)} ~ {min(int(f * videoProcess_frameRatio + videoProcess_mixCount), videoInput_frameCount) - 1} of {int(f * videoProcess_frameRatio)} ~ {int((f + 1) * videoProcess_frameRatio) - 1}",
            total=min(int(f * videoProcess_frameRatio + videoProcess_mixCount), videoInput_frameCount)
            - int(f * videoProcess_frameRatio),
        )
        frameMixedCount = 0
        frameMixed = []
        # framesToMix = []

        for f2 in range(
            int(f * videoProcess_frameRatio),
            min(int(f * videoProcess_frameRatio + videoProcess_mixCount), videoInput_frameCount),
        ):
            frameCurrent = cv2.cvtColor(GetFrame(f2, lastIndex), cv2.COLOR_BGR2Lab).astype(numpy.float32)
            # framesToMix.append(cv2.cvtColor(GetFrame(f2, lastIndex), cv2.COLOR_BGR2Lab).astype(numpy.float32))
            lastIndex = f2
            if frameMixedCount == 0:
                frameMixed = frameCurrent
            else:
                frameMixed = frameMixed * (frameMixedCount / (1 + frameMixedCount)) + frameCurrent * (
                    1 / (1 + frameMixedCount)
                )
            frameMixedCount += 1
            progress.update(small_task, advance=1)
        # frameMixed = cv2.cvtColor(numpy.mean(framesToMix, axis=0).astype(numpy.uint8), cv2.COLOR_Lab2BGR)
        frameMixed = cv2.cvtColor(frameMixed.astype(numpy.uint8), cv2.COLOR_Lab2BGR)
        videoOutput.write(frameMixed)
        progress.update(big_task, advance=1)

videoInput.release()
videoOutput.release()
rich.print("已生成帧混合视频.")