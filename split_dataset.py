import os
import random
import shutil

random.seed(360)  # Same split on everyone's computer

# Run draw_mouse.py first. This copies its images, yolo_dataset stays as it is
YOLO_DATASET_DIR = "yolo_dataset"
YOLO_SPLIT_DIR = "yolo_split"
GROUPS = ["train", "val", "test"]

# Each source is split 60/20/20 on its own so every group gets the same mix
SOURCES = {
    "human": [
        "ours_human",
        "sapi",  # Before Delbot because its people stay whole, Delbot evens out the totals
        "delbot_human_circles_human_fast",
        "delbot_human_circles_human_pc1",
        "delbot_human_circles_human_pc2_pad",  # Before pc2 so it isn't counted as pc2
        "delbot_human_circles_human_pc2",
        "delbot_human_circles_human_tel",
        "delbot_human_circles_human_vm",
    ],
    "bot": [
        "ours_bot_bot_easy",
        "ours_bot_bot_hard",
        "bot_pyhm",
        "bot_naturalmouse",
        "bot_pynput",
        "bot_gan",
    ],
}

def list_images(folder):
    if not os.path.isdir(folder):
        raise SystemExit(f"ERROR: {folder} not found. Run draw_mouse.py first.")
    return sorted(name for name in os.listdir(folder) if name.endswith(".jpg"))

def find_source(image, class_name):
    for source in SOURCES[class_name]:
        if image.startswith(source + "_"):
            return source
    raise SystemExit(f"ERROR: {image} doesn't belong in the dataset. Medium files and old images aren't allowed.")

def person_key(image):
    # SapiMouse people have several sessions, so all of a person's go in the same group
    return image.split("_session")[0] if image.startswith("sapi_") else image

def split_class(class_name):
    by_source = {source: {} for source in SOURCES[class_name]}
    for image in list_images(os.path.join(YOLO_DATASET_DIR, class_name)):
        source = find_source(image, class_name)
        by_source[source].setdefault(person_key(image), []).append(image)

    placed = {group: 0 for group in GROUPS}
    seen = 0
    for source, people in by_source.items():
        if not people:
            raise SystemExit(f"ERROR: no {source} images found in {YOLO_DATASET_DIR}/{class_name}")

        # Aim for 60/20/20 of everything so far, which keeps the final totals exact
        seen += sum(len(images) for images in people.values())
        val = test = round(seen * 0.2)
        wanted = {"train": seen - val - test, "val": val, "test": test}
        need = {group: wanted[group] - placed[group] for group in GROUPS}

        keys = list(people)
        random.shuffle(keys)
        counts = {group: 0 for group in GROUPS}
        for key in keys:
            group = max(need, key=need.get)
            for image in people[key]:
                shutil.copy2(os.path.join(YOLO_DATASET_DIR, class_name, image),
                             os.path.join(YOLO_SPLIT_DIR, group, class_name, image))
            need[group] -= len(people[key])
            placed[group] += len(people[key])
            counts[group] += len(people[key])
        print(f"  {source:<38}{counts['train']:>6}{counts['val']:>6}{counts['test']:>6}")
    print(f"  {class_name + ' total':<38}{placed['train']:>6}{placed['val']:>6}{placed['test']:>6}")

def check_split():
    totals = {}
    for class_name in SOURCES:
        originals = list_images(os.path.join(YOLO_DATASET_DIR, class_name))
        split = {group: list_images(os.path.join(YOLO_SPLIT_DIR, group, class_name)) for group in GROUPS}
        copied = [image for group in GROUPS for image in split[group]]

        if sorted(copied) != originals:
            raise SystemExit(f"ERROR: every {class_name} image must be in exactly one group")

        val = test = round(len(originals) * 0.2)
        totals[class_name] = {"train": len(originals) - val - test, "val": val, "test": test}
        for group in GROUPS:
            if len(split[group]) != totals[class_name][group]:
                raise SystemExit(f"ERROR: wrong number of {class_name} images in {group}")
            if not any(image.startswith("ours_") for image in split[group]):
                raise SystemExit(f"ERROR: none of our own {class_name} images are in {group}")

        people = [{person_key(image) for image in split[group] if image.startswith("sapi_")} for group in GROUPS]
        if sum(len(group) for group in people) != len(set.union(*people)):
            raise SystemExit("ERROR: a SapiMouse person is in more than one group")

    if totals["human"] != totals["bot"]:
        raise SystemExit("ERROR: human and bot counts don't match")

shutil.rmtree(YOLO_SPLIT_DIR, ignore_errors=True)  # Start clean so re-runs don't pile up
for group in GROUPS:
    for class_name in SOURCES:
        os.makedirs(os.path.join(YOLO_SPLIT_DIR, group, class_name), exist_ok=True)

print(f"  {'':<38}{'train':>6}{'val':>6}{'test':>6}")
for class_name in SOURCES:
    split_class(class_name)

check_split()
print("Done!")
