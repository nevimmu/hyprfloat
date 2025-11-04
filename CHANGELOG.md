## 0.4.2 (2025-11-04)

### Fix

- properly tile a term when moving it to a different workspace
- add better to logic to handle menu and not tile them
- ensure fallback values for environment variables and database queries

## 0.4.1 (2025-10-23)

### Fix

- ignore new window if its class isn't in terminals
- term windows properly tile when changing workspaces

## 0.4.0 (2025-10-18)

### Feat

- added regex the the ignore_titles
- new window will always tile to the right

## 0.3.2 (2025-10-16)

### Fix

- handle event parsing error and add support for window title changes
- ensure only visible windows are considered for floating in handle_change
- improve window management for window closing without a closewindow event
- improve window handling logic for ignore and tiled states

## 0.3.1 (2025-10-14)

### Fix

- new window with a ignre_titles are now properly ignored

## 0.3.0 (2025-10-11)

### Feat

- added an option to offset the terminal
- **hyprfloat**: add ignore_tiltle: window with a mathcing title will be ignored and not tiled

### Fix

- **hyprfloat**: fix issue where multiple events were taken at once instead of just one at a time

### Refactor

- **handle_change**: cleanup the logic

## 0.2.3 (2025-10-09)

### Fix

- properly tag the window when floating/tiling

### Refactor

- **hyprfloat**: main loop use a class, moved get_default to db_helper

## 0.2.2 (2025-10-08)

### Fix

- **hyprfloat**: new floating window not in the list won't be tiled automaticaly

## 0.2.1 (2025-10-08)

### Fix

- **hyprfloat**: menu window are now ignored

## 0.2.0 (2025-10-07)

### Feat

- **hyprfloat**: hyprfloat now remember term that are set to be tiled and don't auto-float them

### Fix

- **hyprfloat**: now tiling to the right
- **hyprfloat**: when moving to a workplace with a tiled term, make it float

## 0.1.0 (2025-10-07)

### Feat

- **hyprfloat**: first commit... bit late
