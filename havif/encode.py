from sh import avifenc, convert, avifdec
import tempfile
import os
import logging
import argparse
import subprocess
import shutil


logging.basicConfig(level=logging.INFO)

HEADER_BYTES = 284

parser = argparse.ArgumentParser(description='Convert image to headerless avif.')
parser.add_argument('image', metavar='image', type=str,
                    help='Path to image')
# parser.add_argument('--res', dest='res',
#                     default=240,
#                     help='max image resolution')

parser.add_argument('--auto', dest='auto', default=True, action=argparse.BooleanOptionalAction, help="attempts to get 2k output by lowering the quality")
parser.add_argument('--min', dest='min',
                    default=15,
                    help='min avif quantization')
parser.add_argument('--max', dest='max',
                    default=63,
                    help='max avif quantization')
parser.add_argument('-x', dest='x',
                    default=240,
                    help='max x size of image')
parser.add_argument('--size', dest='size',
                    default=2600,
                    help='max file size for auto mode')

args = parser.parse_args()




# create temp folder to work within
with tempfile.TemporaryDirectory() as tmp:
    resized_path = os.path.join(tmp, 'resized_image.png')
    avif_path = os.path.join(tmp, 'avif.avif')
    avif_l_path = os.path.join(tmp, 'avif.havif')
    avif_sample_path = os.path.join(tmp, 'avif_restored.avif')
    sample_path = os.path.join(tmp, 'avif.png')
    
    logging.info(f"Temp resized image path: {resized_path}")

    logging.info(f"Converting : {args.image}")
    convert_output = convert(args.image, "-strip", "-resize", f"{args.x}x", resized_path)
    logging.info(f"Convert output:\n{convert_output}")
    logging.info(f"Converted image")

    logging.info(f"Converting to avif")
    if args.auto == False:
        avif_output = avifenc("-d", "8", "-y","420","--min",args.min,"--max",args.max,resized_path, avif_path)
    else:
        for q in range(0, 63):
            avif_output = avifenc("-d", "8", "-y","420","--min",q,"--max",args.max,resized_path, avif_path)
            logging.info(f"Headed AVIF filesize: {os.path.getsize(avif_path)}")
            if os.path.getsize(avif_path) < int(args.size):
                break
    logging.info(f"avif output: \n{avif_output}")



    # strip header
    with open(avif_path, "rb") as avif_file:
        avif_file.seek(198)
        x = avif_file.read(2)
        avif_file.seek(202)
        y = avif_file.read(2)
        avif_file.seek(HEADER_BYTES)
        data = avif_file.read()
        with open(avif_l_path, "wb") as havif_file:
            havif_file.write(x)
            havif_file.write(y)
            havif_file.write(data)

    # get header
    with open("header.bytes", "rb") as header_file:
        header = header_file.read()

    # put the header back on to make sure it still works
    with open(avif_l_path, "rb") as havif_file:
        data = header
        x = havif_file.read(2)
        y = havif_file.read(2)
        payload = havif_file.read()
        length = len(payload)
        logging.info(f"payload section is {length} bytes long")
        data += payload
        with open(avif_sample_path,"wb") as sample_avif_file:
            sample_avif_file.write(data)
            logging.info(f"patching file sizes")
            sample_avif_file.seek(124)
            sample_avif_file.write((length+2).to_bytes(4, byteorder='big'))
            sample_avif_file.seek(274)
            sample_avif_file.write((length+8+2).to_bytes(4, byteorder='big')) # not sure why plus 2?
            sample_avif_file.seek(198)
            sample_avif_file.write(x)
            sample_avif_file.seek(202)
            sample_avif_file.write(y)

            logging.info(f"patched")


    logging.info("generating")
    avifdec(avif_sample_path,sample_path)
    logging.info("sample generated")


    shutil.copyfile(sample_path, f"{args.image}.avifsample.png")
    shutil.copyfile(avif_l_path, f"{args.image}.havif")

    # open sample
    subprocess.call(('open', f"{args.image}.avifsample.png"))


    logging.info(f"Original filesize: {os.path.getsize(args.image)}")
    logging.info(f"Resized filesize: {os.path.getsize(resized_path)}")
    logging.info(f"Headed AVIF filesize: {os.path.getsize(avif_path)}")
    logging.info(f"Headerless AVIF filesize: {os.path.getsize(avif_l_path)}")

# convert original.png -resize 100x100! new.png