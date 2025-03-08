from flask import Flask, request, jsonify, abort

app = Flask("lab02")
products_dict = {}
current_id = 0  


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Product not found"}), 404


@app.route("/product", methods=["POST"])
def add_product():
    global current_id

    if not request.is_json:
        return jsonify({"error": "Request body must be JSON"}), 400

    data = request.get_json()
    name = data.get("name")
    description = data.get("description")

    if not name:
        return jsonify({"error": "Field 'name' is required"}), 400

    
    current_id += 1
    new_product_id = current_id

    new_product = {
        "id": new_product_id,
        "name": name,
        "description": description if description else ""
    }

    products_dict[new_product_id] = new_product

    return jsonify(new_product), 201

@app.route("/product/<int:product_id>", methods=["GET"])
def get_product(product_id):

    product = products_dict.get(product_id)
    if not product:
        abort(404)
    return jsonify(product), 200


@app.route("/product/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    if not request.is_json:
        return jsonify({"error": "Request body must be JSON"}), 400

    product = products_dict.get(product_id)
    if not product:
        abort(404)

    data = request.get_json()

    
    if "name" in data:
        product["name"] = data["name"]
    if "description" in data:
        product["description"] = data["description"]

    products_dict[product_id] = product
    return jsonify(product), 200

@app.route("/product/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    product = products_dict.pop(product_id, None)
    if not product:
        abort(404)
    return jsonify(product), 200

@app.route("/products", methods=["GET"])
def get_all_products():
    return jsonify(list(products_dict.values())), 200


app.run(debug=True)


