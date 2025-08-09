import streamlit as st
import numpy as np
import random
from collections import deque, defaultdict

st.set_page_config(layout="wide", page_title="Queens Regions Puzzle")

# ---------- Helpers ----------
def make_contiguous_regions(n, n_regions=None, seed=None):
    random.seed(seed)
    if n_regions is None:
        n_regions = max(4, n)  # default number of regions
    # choose initial seeds at distinct positions
    seeds = set()
    while len(seeds) < n_regions:
        seeds.add((random.randrange(n), random.randrange(n)))
    seeds = list(seeds)
    region_id = [[None]*n for _ in range(n)]
    frontiers = {i: deque() for i in range(len(seeds))}
    for i, (r,c) in enumerate(seeds):
        region_id[r][c] = i
        # add neighbors
        for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
            rr,cc = r+dr, c+dc
            if 0<=rr<n and 0<=cc<n and region_id[rr][cc] is None:
                frontiers[i].append((rr,cc))
    cells_left = n*n - len(seeds)
    while cells_left>0:
        # pick a random non-empty frontier
        non_empty = [i for i,q in frontiers.items() if q]
        if not non_empty:
            # fill remaining unassigned arbitrarily
            for r in range(n):
                for c in range(n):
                    if region_id[r][c] is None:
                        region_id[r][c] = random.randrange(len(seeds))
                        cells_left -= 1
            break
        i = random.choice(non_empty)
        r,c = frontiers[i].popleft()
        if region_id[r][c] is not None:
            continue
        region_id[r][c] = i
        cells_left -= 1
        for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
            rr,cc = r+dr, c+dc
            if 0<=rr<n and 0<=cc<n and region_id[rr][cc] is None:
                frontiers[i].append((rr,cc))
    # compress region ids to contiguous 0..k-1
    mapping = {}
    k=0
    for r in range(n):
        for c in range(n):
            rid = region_id[r][c]
            if rid not in mapping:
                mapping[rid]=k; k+=1
            region_id[r][c] = mapping[rid]
    return np.array(region_id), k

def no_attack_positions(n, queens):
    """return set of cells attacked by any queen"""
    attacked = set()
    for (r,c) in queens:
        for i in range(n):
            attacked.add((r,i))
            attacked.add((i,c))
        # diagonals
        for dr,dc in ((1,1),(1,-1),(-1,1),(-1,-1)):
            rr,cc = r+dr, c+dc
            while 0<=rr<n and 0<=cc<n:
                attacked.add((rr,cc))
                rr += dr; cc += dc
    return attacked

def random_preplace_queens(n, region_map, n_pre=3, seed=None, max_tries=200):
    random.seed(seed)
    placed = set()
    tries = 0
    regions = list(range(region_map.max()+1))
    random.shuffle(regions)
    for rid in regions:
        if len(placed) >= n_pre:
            break
        # candidate cells in region
        cells = [(r,c) for r in range(n) for c in range(n) if region_map[r,c]==rid]
        random.shuffle(cells)
        for (r,c) in cells:
            if any((r==pr or c==pc or abs(r-pr)==abs(c-pc)) for pr,pc in placed):
                continue
            placed.add((r,c))
            break
        tries += 1
        if tries > max_tries:
            break
    return placed

def check_solution(n, queens, region_map):
    # one per row, column, region and none attack
    if len(queens) != n:
        return False, "Numărul de regine nu e egal cu N"
    rows = {r for r,c in queens}
    cols = {c for r,c in queens}
    if len(rows)!=n or len(cols)!=n:
        return False, "Două regine pe aceeași linie/coloană"
    # regions
    region_counts = defaultdict(int)
    for (r,c) in queens:
        region_counts[int(region_map[r,c])] += 1
    for rid in range(region_map.max()+1):
        if region_counts[rid] != 1:
            return False, f"Regiunea {rid} are {region_counts[rid]} regine (trebuie 1)"
    # attacks
    attacked = no_attack_positions(n, queens)
    for q in queens:
        # queen should not be attacked by another queen (attacked includes queen positions from others)
        # simpler: pairwise check
        for q2 in queens:
            if q==q2: continue
            r1,c1 = q; r2,c2 = q2
            if r1==r2 or c1==c2 or abs(r1-r2)==abs(c1-c2):
                return False, "Două regine se atacă (linie/coloană/diagonală)"
    return True, "Solutie corectă!"

# ---------- Session state init ----------
if 'seed' not in st.session_state:
    st.session_state.seed = None
if 'n' not in st.session_state:
    st.session_state.n = 7
if 'region_map' not in st.session_state or 'k_regions' not in st.session_state:
    st.session_state.region_map, st.session_state.k_regions = make_contiguous_regions(st.session_state.n, None, seed=st.session_state.seed)
if 'pre_queens' not in st.session_state:
    st.session_state.pre_queens = set()
if 'queens' not in st.session_state:
    st.session_state.queens = set()
if 'marks' not in st.session_state:
    st.session_state.marks = set()  # X marks (impossible)

# ---------- Controls ----------
st.title("Queens × Regions — Puzzle")
col1, col2, col3, col4 = st.columns([1,1,1,1])
with col1:
    n_in = st.number_input("N (grid)", min_value=4, max_value=12, value=st.session_state.n, step=1)
with col2:
    num_regions = st.number_input("Approx. #regiuni", min_value=2, max_value=st.session_state.n*st.session_state.n, value=None if st.session_state.k_regions is None else st.session_state.k_regions)
with col3:
    seed_in = st.text_input("Seed (opțional)", value="" if st.session_state.seed is None else str(st.session_state.seed))
with col4:
    if st.button("New puzzle"):
        try:
            s = int(seed_in) if seed_in.strip()!="" else None
        except:
            s = None
        st.session_state.n = int(n_in)
        st.session_state.seed = s
        st.session_state.region_map, st.session_state.k_regions = make_contiguous_regions(st.session_state.n, None, seed=st.session_state.seed)
        st.session_state.pre_queens = random_preplace_queens(st.session_state.n, st.session_state.region_map, n_pre=max(1, st.session_state.n//3), seed=st.session_state.seed)
        st.session_state.queens = set(st.session_state.pre_queens)
        st.session_state.marks = set()

if st.button("Reset current"):
    st.session_state.queens = set(st.session_state.pre_queens)
    st.session_state.marks = set()

hint_col, check_col = st.columns([1,1])
with hint_col:
    if st.button("Hint (marchează X celule imposibile)"):
        attacked = no_attack_positions(st.session_state.n, st.session_state.queens)
        # also mark cells in regions that already have a queen
        region_has = {int(st.session_state.region_map[r,c]) for r,c in st.session_state.queens}
        new_marks = set()
        for r in range(st.session_state.n):
            for c in range(st.session_state.n):
                if (r,c) in st.session_state.queens: continue
                if (r,c) in attacked: new_marks.add((r,c))
                if int(st.session_state.region_map[r,c]) in region_has: new_marks.add((r,c))
        st.session_state.marks = new_marks
with check_col:
    if st.button("Check"):
        ok, msg = check_solution(st.session_state.n, st.session_state.queens, st.session_state.region_map)
        if ok:
            st.success(msg)
        else:
            st.error(msg)

# ---------- Grid UI ----------
n = st.session_state.n
region_map = st.session_state.region_map
k_regions = region_map.max()+1

# create colors for regions (CSS)
def color_from_idx(i):
    random.seed(i)
    h = int((random.random()*360))
    return f"hsl({h}deg 80% 80%)"

region_colors = [color_from_idx(i) for i in range(k_regions)]

grid_cols = st.columns(n)
# render grid using buttons in rows for a compact look
for r in range(n):
    row_cols = st.columns(n)
    for c in range(n):
        rid = int(region_map[r,c])
        bg = region_colors[rid]
        label = ""
        is_pre = (r,c) in st.session_state.pre_queens
        is_q = (r,c) in st.session_state.queens
        is_mark = (r,c) in st.session_state.marks
        if is_q:
            label = "♛"
        elif is_mark:
            label = "X"
        key = f"cell_{r}_{c}"
        style = f"background-color:{bg}; padding:6px; border:1px solid #888; min-height:44px; text-align:center;"
        if is_pre:
            style += " font-weight:bold; border:2px solid #000;"
        # button toggles queen (but prevent removing pre-placed queens)
        if row_cols[c].button(label if label!="" else " ", key=key):
            if is_pre:
                # ignore toggles on pre-placed queens (immutable)
                pass
            else:
                if (r,c) in st.session_state.queens:
                    st.session_state.queens.remove((r,c))
                else:
                    st.session_state.queens.add((r,c))
                # clear marks on change
                st.session_state.marks = set()
        # overlay small info: region id (for debugging)
        # show region id faintly
        row_cols[c].markdown(f"<div style='{style}'><small style='opacity:.5'>R{rid}</small></div>", unsafe_allow_html=True)

# ---------- Footer: current status ----------
st.write("Regine plasate:", sorted(list(st.session_state.queens)))
st.write("Regiuni:", k_regions, " N =", n)
