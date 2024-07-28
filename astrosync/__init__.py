import os
import hashlib
import logging
import io
from dataclasses import dataclass

_EXT = ".txt"
_DATE_NUM_STORIES = ["journal"]

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

@dataclass
class FileSpec:
    full_path: str
    file_story: str
    dir_story: str
    hash: str
    year: str
    num: int
    src_date_num: int

class Syncer:
    def __init__(self, src: str, dst: str, dry_run: bool):
        self.src = src
        self.dst = dst
        self.dry_run = dry_run
        self.src_files = self.get_src_files()
        self.dst_files = self.get_dst_files()
        self.dst_dirs = self.get_dst_dirs()

    def get_src_files(self) -> list[FileSpec]:
        src_files = list[FileSpec]()
        dirs = [ self.src + "/" + x for x in ["A", "B", "C"]]
        for d in dirs:
            if not os.path.isdir(d):
                log.debug("Expected dir %s but it wasn't found" % (d))
                continue
            for f in os.listdir(d):
                full_path = os.path.join(d, f)
                spec = filespec_from_postbox(full_path)
                if spec.file_story is None:
                    log.debug("Skipping unexpected non-story file: %s" % (full_path))
                src_files.append(spec)

        src_files.sort(key=lambda x: x.full_path)
        return src_files

    def get_dst_files(self) -> list[FileSpec]:
        dst_files = list[FileSpec]()
        for d in os.listdir(self.dst):
            fd = os.path.join(self.dst, d)
            if not os.path.isdir(fd):
                log.debug("Skipping unexpected non-dir file: %s" % (fd))
                continue
            for f in os.listdir(fd):
                full_path = os.path.join(fd, f)
                spec = filespec_from_writing(full_path)
                if is_writing_file(spec):
                    dst_files.append(spec)
                else:
                    log.debug("Skipping unexpected non-writing file: %s" % (full_path))

        dst_files.sort(key=lambda x: x.full_path)
        return dst_files

    def get_dst_dirs(self) -> list[str]:
        dst_dirs = list[str]()
        for d in os.listdir(self.dst):
            fd = os.path.join(self.dst, d)
            if os.path.isdir(fd):
                dst_dirs.append(fd)

        return dst_dirs

    def sync(self):
        uniq_dir_story = { os.path.basename(x) for x in self.dst_dirs }

        for story in uniq_dir_story:
            wt_story = [x for x in self.dst_files if x.dir_story == story]
            nums = [x.num for x in wt_story if x.num is not None]
            if len(nums) > 0:
                max_num = max(nums)
            else:
                max_num = 0
            hashes = {x.hash: True for x in wt_story}
            for pb in self.src_files:
                if pb.file_story != story:
                    continue

                if pb.hash in hashes:
                    log.debug("A file for %s with this hash exists" % (story))
                    continue

                # For "stories" like those in "journal" we assume the number is a
                # unique date instead of an incrementing version.
                if pb.file_story in _DATE_NUM_STORIES:
                    resolved_pb_num = pb.num if pb.num is not None else pb.src_date_num
                    if resolved_pb_num is None:
                        log.error("Skipping date_num story with no date: %s" % (pb))
                        continue

                    dst_path = self.convert_pb_to_wt_path(pb, resolved_pb_num)
                    dst_spec = filespec_copy_into_wt(pb, resolved_pb_num, dst_path)
                else:
                    max_num = max_num + 1
                    dst_path = self.convert_pb_to_wt_path(pb, max_num)
                    dst_spec = filespec_copy_into_wt(pb, max_num, dst_path)

                if os.path.exists(dst_spec.full_path):
                    log.error("Refusing to copy over %s with %s" % (dst_spec.full_path, pb.full_path))
                    continue

                if self.dry_run:
                    log.warning("Dry run, would copy from %s to %s" % (pb.full_path, dst_spec.full_path))
                else:
                    print("Copying %s to %s" % (pb.full_path, dst_spec.full_path))
                    with open(pb.full_path, "rb") as fin:
                        with open(dst_spec.full_path, "wb") as fout:
                            while True:
                                b = fin.read(io.DEFAULT_BUFFER_SIZE)
                                if len(b) == 0:
                                    break
                                fout.write(b)

    def convert_pb_to_wt_path(self, pb_spec: FileSpec, num: int) -> str:
        if pb_spec.file_story in _DATE_NUM_STORIES:
            filename = f"{pb_spec.file_story}{num:04d}{_EXT}"
        else:
            filename = f"{pb_spec.file_story}{num:02d}{_EXT}"

        return os.path.join(self.dst, pb_spec.file_story, filename)

def filespec_from_postbox(full_path: str) -> FileSpec:
    file_story = compute_postbox_story(full_path)
    return FileSpec(
        full_path, file_story, None,
        compute_hash(full_path), compute_postbox_year(full_path),
        compute_num(full_path, len(file_story) + 11),
        compute_src_date_num(full_path),
    )

def filespec_from_writing(full_path: str) -> FileSpec:
    file_story = compute_writing_file_story(full_path)
    return FileSpec(
        full_path, file_story, compute_writing_dir_story(full_path),
        compute_hash(full_path), compute_writing_year(full_path),
        compute_num(full_path, len(file_story)) if file_story is not None else None,
        None,
    )

def filespec_copy_into_wt(pb_spec: FileSpec, num: int, full_path: str) -> FileSpec:
    return FileSpec(
        full_path, pb_spec.file_story, pb_spec.dir_story, pb_spec.hash,
        pb_spec.year, num, None,
    )

def compute_postbox_story(full_path: str) -> str:
    basename = os.path.basename(full_path)
    no_date = basename[11:-4]

    i = 0
    for char in no_date:
        i += 1
        if ord(char) not in range(ord('A'), ord('z')):
            return no_date[:i-1]

    return no_date

def compute_hash(full_path: str) -> str:
    if os.path.isdir(full_path):
        return None

    h = hashlib.sha256()
    with open(full_path, mode="rb") as f:
        h.update(f.read())

    return h.hexdigest()

def compute_postbox_year(full_path: str) -> str:
    basename = os.path.basename(full_path)
    return basename[0:4]

def compute_writing_dir_story(full_path: str) -> str:
    dirname = os.path.dirname(full_path)
    return os.path.split(dirname)[1]

def compute_writing_file_story(full_path: str) -> str:
    basename = os.path.basename(full_path)
    i = 0
    for char in basename:
        i += 1
        if ord(char) not in range(ord('A'), ord('z')):
            return basename[:i-1]
    return None

def compute_writing_year(full_path: str) -> str:
    dirname = os.path.dirname(full_path)
    return os.path.split(os.path.split(dirname)[0])[1]

def compute_src_date_num(full_path: str) -> int:
    basename = os.path.basename(full_path)
    mm = basename[5:7]
    dd = basename[8:10]
    src_date_num = int(mm) * 100 + int(dd)
    return src_date_num

def compute_num(full_path: str, num_start_idx: int) -> int:

    if num_start_idx is None:
        log.error("Cannot compute num for %s" % (full_path))
        return None

    basename = os.path.basename(full_path)
    fn = os.path.splitext(basename)[0]
    try:
        return int(fn[num_start_idx:])
    except ValueError as e:
        log.debug("Cannot parse num for %s due to %s" % (full_path , e))

    return None

def is_writing_file(spec: FileSpec) -> bool:
    return spec.dir_story == spec.file_story or spec.file_story == "draft"
