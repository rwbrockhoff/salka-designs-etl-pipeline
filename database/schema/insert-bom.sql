-- Insert bill of materials data using product_sku as foreign key
-- Used for initial database set up
-- BEGIN/COMMIT ensures one transaction (no partial insertion)

BEGIN;

INSERT INTO bill_of_materials 
    (product_sku, material_piece, material_color, material_quantity, is_fabric) 
VALUES 
    -- Wildflower Edition Lupine
    ('SQ8266292', 'Custom Pattern', 'Bluebell', 1, true),
    ('SQ8266292', 'Liner', 'White', 1, true),
    ('SQ8266292', 'Inside/Outside Pocket', 'Dark Blue', 2, true),
    ('SQ8266292', 'Wings', 'Dark Blue', 2, true),
    ('SQ8266292', 'Front Pocket - Top', 'Dark Blue', 1, true),
    ('SQ8266292', 'Front Pocket - Bottom', 'Bluebell', 1, true),
    
    -- Wildflower Edition Paintbrush
    ('SQ9055246', 'Custom Pattern', 'Peach', 1, true),
    ('SQ9055246', 'Liner', 'White', 1, true),
    ('SQ9055246', 'Inside/Outside Pocket', 'Red', 2, true),
    ('SQ9055246', 'Wings', 'Red', 2, true),
    ('SQ9055246', 'Front Pocket - Top', 'Red', 1, true),
    ('SQ9055246', 'Front Pocket - Bottom', 'Peach', 1, true),
    
    -- Honey Pinecone (Brown)
    ('SQ7558466', 'Custom Pattern', 'Brown', 1, true),
    ('SQ7558466', 'Inside Pocket', 'Black', 1, true),
    ('SQ7558466', 'Outer Mesh', 'Black', 1, true),
    ('SQ7558466', 'Wings', 'Black', 2, true),
    
    -- Wild Lupine (Purple)
    ('SQ1399946', 'Custom Pattern', 'Purple', 1, true),
    ('SQ1399946', 'Inside Pocket', 'Black', 1, true),
    ('SQ1399946', 'Outer Mesh', 'Black', 1, true),
    ('SQ1399946', 'Wings', 'Black', 2, true),
    
    -- Midnight Pine (Black)
    ('SQ2405814', 'Custom Pattern', 'Black', 1, true),
    ('SQ2405814', 'Inside Pocket', 'Black', 1, true),
    ('SQ2405814', 'Outer Mesh', 'Black', 1, true),
    ('SQ2405814', 'Wings', 'Black', 2, true),
    
    -- Misty Fern (Green)
    ('SQ5375200', 'Custom Pattern', 'Ranger Green', 1, true),
    ('SQ5375200', 'Inside Pocket', 'Black', 1, true),
    ('SQ5375200', 'Outer Mesh', 'Black', 1, true),
    ('SQ5375200', 'Wings', 'Black', 2, true),
    
    -- Alpine Lake (Teal)
    ('SQ0934585', 'Custom Pattern', 'Teal', 1, true),
    ('SQ0934585', 'Inside Pocket', 'Black', 1, true),
    ('SQ0934585', 'Outer Mesh', 'Black', 1, true),
    ('SQ0934585', 'Wings', 'Black', 2, true);

COMMIT;