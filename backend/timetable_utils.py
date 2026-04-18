import random

DAYS = 6
SLOTS = 6


def get_slot_code(day, slot):
    days = ["M", "T", "W", "TH", "F", "S"]
    return f"{days[day]}{slot+1}"


def build_constraints(existing_timetables):
    teacher_busy = {}
    room_busy = {}

    for doc in existing_timetables:
        tt = doc.get("timetable", {})

        for d in range(DAYS):
            day = f"day{d}"
            if day not in tt:
                continue

            for s in range(SLOTS):
                slot_key = f"slot{s}"
                if slot_key not in tt[day]:
                    continue

                cell = tt[day][slot_key]

                for key in cell:
                    entry = cell[key]
                    if not entry:
                        continue

                    teacher = entry.get("teacherId")
                    room = entry.get("room")
                    slots = entry.get("slot")

                    slot_list = slots if isinstance(slots, list) else [slots]

                    for sl in slot_list:
                        if teacher:
                            teacher_busy.setdefault(teacher, set()).add(sl)
                        if room:
                            room_busy.setdefault(room, set()).add(sl)

    return teacher_busy, room_busy


def is_valid_global(teacherId, room, d, s, teacher_busy, room_busy):
    slot = get_slot_code(d, s)

    if teacherId in teacher_busy and slot in teacher_busy[teacherId]:
        return False

    if room in room_busy and slot in room_busy[room]:
        return False

    return True


def get_teacher(subject_name, subjects):
    for s in subjects:
        name = s.get("subject_name")

        if name and name.strip().upper() == subject_name.strip().upper():
            teacher_id = (
                s.get("faculty_id") or
                s.get("other_faculty_id") or
                s.get("facultyId") or
                s.get("teacherId")
            )

            if not teacher_id:
                return "Unknown", "T-NA"

            return teacher_id, teacher_id

    return "Unknown", "T-NA"


def get_lab(subject_name, subjects):
    for s in subjects:
        name = s.get("subject_name")

        if name and name.strip().upper() == subject_name.strip().upper():
            return s.get("room") or "LAB"

    return "LAB"


def normalize(subjects):
    for s in subjects:
        s["type"] = str(s.get("type", "")).lower()
        s["batch_required"] = str(s.get("batch_required", "")).lower()
        s["hours"] = int(s.get("hours", 0))
    return subjects


def is_batch_lab(s):
    return s["type"] == "lab" and s["batch_required"] in ["yes", "true", "1"]


def is_common_lab(s):
    return s["type"] == "lab" and s["batch_required"] in ["no", "false", "0"]


def is_theory(s):
    return s["type"] == "theory"


def get_batches(subjects):
    for s in subjects:
        if is_batch_lab(s):
            return int(s.get("batches", 1))
    return 1


def empty_tt(batches):
    return [
        [{"COMMON": None, **{f"B{b+1}": None for b in range(batches)}}
         for _ in range(SLOTS)]
        for _ in range(DAYS)
    ]


def is_slot_empty(tt, d, s):
    if tt[d][s]["COMMON"]:
        return False
    for k in tt[d][s]:
        if k != "COMMON" and tt[d][s][k]:
            return False
    return True