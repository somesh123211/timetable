import random

DAYS = 6
SLOTS = 6


# =========================
# 🔥 NEW HELPERS (SAFE ADD)
# =========================
def get_slot_code(day, slot):
    days = ["M", "T", "W", "TH", "F", "S"]
    return f"{days[day]}{slot+1}"


# =========================
# 🔥 FIXED HELPERS (IMPORTANT)
# =========================
def get_teacher(subject_name, subjects):
    
    for s in subjects:

        name = s.get("subject_name")

        if name and name.strip().upper() == subject_name.strip().upper():

            # 🔥 use faculty_id as teacherId
            teacher_id = s.get("faculty_id")

            # 🔥 optional: fetch teacher name later from users collection
            teacher_name = teacher_id if teacher_id else "Unknown"

            return teacher_name, teacher_id if teacher_id else "T-NA"

    return "Unknown", "T-NA"

def get_lab(subject_name, subjects):
    
    for s in subjects:

        name = s.get("subject_name")

        if name and name.strip().upper() == subject_name.strip().upper():

            # 🔥 your DB uses 'room'
            room = s.get("room")

            return room if room else "LAB"

    return "LAB"

# =========================
# NORMALIZE
# =========================
def normalize(subjects):
    for s in subjects:
        s["type"] = str(s.get("type", "")).lower()
        s["batch_required"] = str(s.get("batch_required", "")).lower()
        s["hours"] = int(s.get("hours", 0))
    return subjects


# =========================
# TYPE CHECKS
# =========================
def is_batch_lab(s):
    return s["type"] == "lab" and s["batch_required"] in ["yes", "true", "1"]


def is_common_lab(s):
    return s["type"] == "lab" and s["batch_required"] in ["no", "false", "0"]


def is_theory(s):
    return s["type"] == "theory"


# =========================
# STRUCTURE
# =========================
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


# =========================
# 🔥 BATCH LABS (UNCHANGED LOGIC)
# =========================
def place_batch_labs(tt, batch_labs, batches, subjects):

    subjects_names = [s["subject_name"] for s in batch_labs]
    n = len(subjects_names)

    sessions = []
    for s in batch_labs:
        for _ in range(s["hours"] // 2):
            sessions.append(s["subject_name"])

    total_sessions = len(sessions)

    day_slots = {d: [] for d in range(DAYS)}

    d = 0
    for i in range(total_sessions):
        day_slots[d].append(i)
        d = (d + 1) % DAYS

    for d in day_slots:
        random.shuffle(day_slots[d])

    rotation = 0

    for d in range(DAYS):

        lab_count = 0

        for session_index in day_slots[d]:

            if lab_count >= 2:
                break

            slot_options = [0, 2, 4]
            random.shuffle(slot_options)

            for s in slot_options:

                if s >= SLOTS - 1:
                    continue

                if not (is_slot_empty(tt, d, s) and is_slot_empty(tt, d, s+1)):
                    continue

                for b in range(batches):

                    sub = subjects_names[(b + rotation) % n]

                    teacher, teacherId = get_teacher(sub, subjects)
                    lab_room = get_lab(sub, subjects)

                    entry = {
                        "subject": sub,
                        "teacher": teacher,
                        "teacherId": teacherId,
                        "type": "lab",
                        "room": lab_room,
                        "slot": [
                            get_slot_code(d, s),
                            get_slot_code(d, s+1)
                        ]
                    }

                    tt[d][s][f"B{b+1}"] = entry
                    tt[d][s+1][f"B{b+1}"] = entry

                rotation += 1
                lab_count += 1
                break


# =========================
# COMMON LABS (UNCHANGED LOGIC)
# =========================
def place_common_labs(tt, common_labs, subjects):

    labs_per_day = [0] * DAYS

    for d in range(DAYS):
        for s in range(SLOTS):
            if tt[d][s]["COMMON"] and tt[d][s]["COMMON"]["type"] == "lab":
                labs_per_day[d] += 1

            for k in tt[d][s]:
                if k != "COMMON" and tt[d][s][k] and tt[d][s][k]["type"] == "lab":
                    labs_per_day[d] += 1
                    break

        labs_per_day[d] = labs_per_day[d] // 2

    for sub in common_labs:

        sessions = sub["hours"] // 2

        for _ in range(sessions):

            placed = False

            for d in range(DAYS):

                if labs_per_day[d] >= 2:
                    continue

                for s in [0, 2, 4]:

                    if not (is_slot_empty(tt, d, s) and is_slot_empty(tt, d, s+1)):
                        continue

                    teacher, teacherId = get_teacher(sub["subject_name"], subjects)
                    lab_room = get_lab(sub["subject_name"], subjects)

                    entry = {
                        "subject": sub["subject_name"],
                        "teacher": teacher,
                        "teacherId": teacherId,
                        "type": "lab",
                        "room": lab_room,
                        "slot": [
                            get_slot_code(d, s),
                            get_slot_code(d, s+1)
                        ]
                    }

                    tt[d][s]["COMMON"] = entry
                    tt[d][s+1]["COMMON"] = entry

                    labs_per_day[d] += 1
                    placed = True
                    break

                if placed:
                    break


# =========================
# THEORY (UNCHANGED LOGIC)
# =========================
def place_theory(tt, theory, subjects):

    pool = []
    for s in theory:
        pool.extend([s["subject_name"]] * s["hours"])

    random.shuffle(pool)

    idx = 0

    for d in range(DAYS):
        used = set()

        for s in range(SLOTS):

            if not is_slot_empty(tt, d, s):
                continue

            for _ in range(len(pool)):
                sub = pool[idx % len(pool)]
                idx += 1

                if sub not in used:

                    teacher, teacherId = get_teacher(sub, subjects)

                    tt[d][s]["COMMON"] = {
                        "subject": sub,
                        "teacher": teacher,
                        "teacherId": teacherId,
                        "type": "theory",
                        "room": "CLASS",
                        "slot": get_slot_code(d, s)
                    }

                    used.add(sub)
                    break


# =========================
# MAIN (UNCHANGED)
# =========================
def generate_timetable(subjects):

    subjects = normalize(subjects)

    batch_labs = []
    common_labs = []
    theory = []

    for s in subjects:
        if is_batch_lab(s):
            batch_labs.append(s)
        elif is_common_lab(s):
            common_labs.append(s)
        elif is_theory(s):
            theory.append(s)

    batches = get_batches(subjects)

    tt = empty_tt(batches)

    place_batch_labs(tt, batch_labs, batches, subjects)
    place_common_labs(tt, common_labs, subjects)
    place_theory(tt, theory, subjects)

    return tt