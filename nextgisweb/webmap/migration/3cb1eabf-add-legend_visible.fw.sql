/*** {
    "revision": "3cb1eabf", "parents": ["3abe311d"],
    "date": "2023-04-19T22:56:36",
    "message": "Add legend_visible"
} ***/

ALTER TABLE webmap
ADD COLUMN legend_visible
VARCHAR(50)
DEFAULT 'default';

ALTER TABLE webmap_item
ADD COLUMN legend_visible
VARCHAR(50)
DEFAULT 'default';
