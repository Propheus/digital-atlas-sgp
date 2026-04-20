#!/usr/bin/env python3
"""Fix category tags and remove duplicates in the built app JS."""
import sys

JS_PATH = "/home/azureuser/digital-atlas-sgp/sgp-atlas-app/app/dist/assets/index-BCz-A6kC.js"

with open(JS_PATH) as f:
    js = f.read()

changes = 0

# Remove the old QSR tag (d&&_&&...)
old_qsr = 'd&&_&&x.jsx("span",{className:"text-[11px] px-2 py-0.5 rounded-full font-semibold",style:{background:"#a855f720",color:"#c084fc"},children:_})'
if old_qsr in js:
    js = js.replace(old_qsr, "null")
    print("Removed QSR tag")
    changes += 1

# Remove Dept Store tag
old_dept = 'p&&x.jsx("span",{className:"text-[11px] px-2 py-0.5 rounded-full font-semibold",style:{background:"#ec489920",color:"#f472b6"},children:"Dept Store"})'
if old_dept in js:
    js = js.replace(old_dept, "null")
    print("Removed Dept Store tag")
    changes += 1

# Remove Gas Station tag (with fuel pump emoji)
old_gas = 'g&&x.jsx("span",{className:"text-[11px] px-2 py-0.5 rounded-full font-semibold",style:{background:"#ef444420",color:"#f87171"},children:"\u26fd Gas Station"})'
if old_gas in js:
    js = js.replace(old_gas, "null")
    print("Removed Gas Station tag")
    changes += 1

if changes > 0:
    with open(JS_PATH, "w") as f:
        f.write(js)
    print(f"Saved {changes} changes")
else:
    print("No changes needed")
