
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    category_id INT REFERENCES categories(id)
);

INSERT INTO categories (name) VALUES ('Electronics'), ('Clothing');
INSERT INTO products (name, price, category_id) VALUES ('Pro Headphones', 199.99, 1);