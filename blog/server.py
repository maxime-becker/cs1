from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List
import json
import os
import datetime

app = FastAPI()

# Répertoire pour stocker les images
UPLOAD_DIRECTORY = "uploaded_images"
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)


# Modèle pour les posts
class Post(BaseModel):
    id: int
    title: str
    image: str
    content: str
    comments: List[str]
    date: str
    likes: int
    ratings: List[int]
    average_rating: float


class PostList(BaseModel):
    posts: List[Post]


# Charger les posts depuis un fichier JSON
def get_post_list_from_file():
    with open('data.json', 'r') as file:
        return PostList(**json.load(file))


def write_post_list(post_list: PostList):
    with open('data.json', 'w') as file:
        json.dump(post_list.dict(), file, indent=2)


# Route pour obtenir tous les posts
@app.get("/posts", response_model=PostList)
def get_posts():
    return get_post_list_from_file()


# Route pour ajouter un commentaire à un post
class Comment(BaseModel):
    comment: str


@app.post("/posts/{post_id}/comments")
def add_comment(post_id: int, comment: Comment):
    post_list = get_post_list_from_file()
    for post in post_list.posts:
        if post.id == post_id:
            post.comments.append(comment.comment)
            write_post_list(post_list)
            return {"message": "Commentaire ajouté"}
    raise HTTPException(status_code=404, detail="Post non trouvé")


# Route pour liker un post
@app.post("/posts/{post_id}/like")
def like_post(post_id: int):
    post_list = get_post_list_from_file()
    for post in post_list.posts:
        if post.id == post_id:
            post.likes += 1
            write_post_list(post_list)
            return {"message": "Like ajouté"}
    raise HTTPException(status_code=404, detail="Post non trouvé")


# Modèle pour la notation
class RatingModel(BaseModel):
    rating: int


# Route pour noter un post
@app.post("/posts/{post_id}/rate")
def rate_post(post_id: int, rating: RatingModel):
    post_list = get_post_list_from_file()

    for post in post_list.posts:
        if post.id == post_id:
            # Ajouter la note et recalculer la moyenne
            post.ratings.append(rating.rating)
            post.average_rating = sum(post.ratings) / len(post.ratings)
            write_post_list(post_list)
            return {"message": "Post noté avec succès"}
    
    raise HTTPException(status_code=404, detail="Post non trouvé")


# Route pour ajouter un nouveau post avec une image
@app.post("/posts")
async def create_post(file: UploadFile = File(...), title: str = Form(...), content: str = Form(...)):
    post_list = get_post_list_from_file()

    # Sauvegarde de l'image
    image_filename = file.filename
    file_location = os.path.join(UPLOAD_DIRECTORY, image_filename)
    with open(file_location, "wb+") as file_object:
        file_object.write(await file.read())

    # Création du nouveau post
    new_post = Post(
        id=len(post_list.posts) + 1,
        title=title,
        image=image_filename,
        content=content,
        comments=[],
        date=datetime.datetime.now().isoformat(),
        likes=0,
        ratings=[],
        average_rating=0.0
    )

    # Ajout du post à la liste
    post_list.posts.append(new_post)
    write_post_list(post_list)
    return {"message": "Post créé", "post": new_post}


# Route pour supprimer un post
@app.delete("/posts/{post_id}")
def delete_post(post_id: int):
    post_list = get_post_list_from_file()

    # Chercher et supprimer le post
    post_to_delete = None
    for post in post_list.posts:
        if post.id == post_id:
            post_to_delete = post
            break

    if post_to_delete:
        post_list.posts.remove(post_to_delete)
        write_post_list(post_list)
        return {"message": "Post supprimé"}
    else:
        raise HTTPException(status_code=404, detail="Post non trouvé")


# Route pour servir les images uploadées
@app.get("/images/{filename}")
async def get_image(filename: str):
    file_path = os.path.join(UPLOAD_DIRECTORY, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Fichier non trouvé")
    return FileResponse(file_path)


# Route pour la page d'accueil (HTML)
@app.get("/", response_class=HTMLResponse)
def get_index():
    with open('index.html', 'r') as file:
        return file.read()


# Route pour la page "À propos" (HTML)
@app.get("/about", response_class=HTMLResponse)
def get_about():
    with open('about.html', 'r') as file:
        return file.read()


# Route pour la page "Contact" (HTML)
@app.get("/contact", response_class=HTMLResponse)
def get_contact():
    with open('contact.html', 'r') as file:
        return file.read()

@app.delete("/posts/{post_id}/comments/{comment_index}")
def delete_comment(post_id: int, comment_index: int):
    post_list = get_post_list_from_file()
    
    # Chercher le post par son ID
    for post in post_list.posts:
        if post.id == post_id:
            # Vérifier que l'index du commentaire existe
            if 0 <= comment_index < len(post.comments):
                # Supprimer le commentaire
                post.comments.pop(comment_index)
                write_post_list(post_list)
                return {"message": "Commentaire supprimé"}
            else:
                raise HTTPException(status_code=400, detail="Index de commentaire non valide")
    raise HTTPException(status_code=404, detail="Post non trouvé")
