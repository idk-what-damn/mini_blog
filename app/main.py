from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from sqlalchemy.exc import IntegrityError

from app.database import get_db, engine, Base
from app.models import User, Article, Comment, Tag, Like
from app.schemas import *
from sqlalchemy import and_, func

load_dotenv()


Base.metadata.create_all(bind=engine)


SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(title="Мини-Блог")


app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")



def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
        request: Request,
        token: Optional[str] = None,
        db: Session = Depends(get_db)
):

    if not token:
        token = request.cookies.get("access_token")

    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None

    user = db.query(User).filter(User.username == username).first()
    return user


@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request, db: Session = Depends(get_db)):
    current_user = await get_current_user(request, db=db)

    articles = db.query(Article).order_by(Article.created_at.desc()).limit(5).all()

    for article in articles:
        article.author = db.query(User).filter(User.id == article.author.id).first()
        article.likes_count = db.query(Like).filter(Like.article_id == article.id).count()
        article.is_liked = False
        if current_user:
            existing_like = db.query(Like).filter(and_(Like.user_id == current_user.id, Like.article_id == article.id)).first()
            article.is_liked = bool(existing_like)

    tags = db.query(Tag).limit(10).all()

    total_likes = db.query(Like).count()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "current_user": current_user,
        "articles": articles,
        "tags": tags,
        "total_likes": total_likes,
    })


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, db: Session = Depends(get_db)):
    current_user = await get_current_user(request, db=db)
    if current_user:
        return RedirectResponse("/", status_code=303)

    return templates.TemplateResponse("login.html", {
        "request": request
    })


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, db: Session = Depends(get_db)):
    current_user = await get_current_user(request, db=db)
    if current_user:
        return RedirectResponse("/", status_code=303)

    return templates.TemplateResponse("register.html", {
        "request": request
    })


@app.get("/articles", response_class=HTMLResponse)
async def articles_page(
        request: Request,
        page: int = 1,
        search: Optional[str] = None,
        tag: Optional[str] = None,
        sort: Optional[str] = "newest",
        db: Session = Depends(get_db)
):
    current_user = await get_current_user(request, db=db)
    limit = 10
    offset = (page - 1) * limit

    query = db.query(Article)

    if search:
        query = query.filter(
            Article.title.contains(search) | Article.content.contains(search)
        )

    if tag:
        tag_obj = db.query(Tag).filter(Tag.name == tag).first()
        if tag_obj:
            query = query.filter(Article.tags.contains(tag_obj))

    if sort == "newest":
        query = query.order_by(Article.created_at.desc())
    elif sort == "oldest":
        query = query.order_by(Article.created_at.asc())
    elif sort == "popular":
        articles = query.all()
        articles_with_likes = []
        for article in articles:
            likes_count = db.query(Like).filter(Like.article_id == article.id).count()
            articles_with_likes.append((article, likes_count))

        articles_with_likes.sort(key=lambda x: x[1], reverse=True)

        sorted_articles = [article for article, likes_count in articles_with_likes]

        total_articles = len(sorted_articles)
        total_pages = (total_articles + limit - 1) // limit

        paginated_articles = sorted_articles[offset:offset + limit]

        articles = []
        for article in paginated_articles:
            article.likes_count = db.query(Like).filter(Like.article_id == article.id).count()
            article.author = db.query(User).filter(User.id == article.author_id).first()
            article.is_liked = False
            if current_user:
                existing_like = db.query(Like).filter(
                    and_(Like.user_id == current_user.id, Like.article_id == article.id)).first()
                article.is_liked = bool(existing_like)
            articles.append(article)

        tags = db.query(Tag).all()

        return templates.TemplateResponse("articles.html", {
            "request": request,
            "current_user": current_user,
            "articles": articles,
            "tags": tags,
            "current_page": page,
            "total_pages": total_pages,
            "search_query": search,
            "current_tag": tag,
            "current_sort": sort
        })

    total_articles = query.count()
    articles = query.offset(offset).limit(limit).all()

    for article in articles:
        article.author = db.query(User).filter(User.id == article.author_id).first()
        article.likes_count = db.query(Like).filter(Like.article_id == article.id).count()
        article.is_liked = False
        if current_user:
            existing_like = db.query(Like).filter(
                and_(Like.user_id == current_user.id, Like.article_id == article.id)).first()
            article.is_liked = bool(existing_like)

    tags = db.query(Tag).all()

    total_pages = (total_articles + limit - 1) // limit

    return templates.TemplateResponse("articles.html", {
        "request": request,
        "current_user": current_user,
        "articles": articles,
        "tags": tags,
        "current_page": page,
        "total_pages": total_pages,
        "search_query": search,
        "current_tag": tag,
        "current_sort": sort
    })



@app.post("/api/articles")
async def create_article_api(
        request: Request,
        title: str = Form(...),
        content: str = Form(...),
        tags: str = Form(""),
        db: Session = Depends(get_db)
):
    current_user = await get_current_user(request, db=db)
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    db_article = Article(
        title=title,
        content=content,
        author_id=current_user.id
    )

    tag_names = [tag.strip() for tag in tags.split(",") if tag.strip()]
    for tag_name in tag_names:
        tag = db.query(Tag).filter(Tag.name == tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.add(tag)
            db.flush()
        db_article.tags.append(tag)

    db.add(db_article)
    db.commit()

    return RedirectResponse(f"/articles/{db_article.id}", status_code=303)
@app.get("/articles/new", response_class=HTMLResponse)
async def create_article_page(
        request: Request,
        db: Session = Depends(get_db)
):
    current_user = await get_current_user(request, db=db)
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    try:
        all_tags = db.query(Tag).all()
    except Exception as e:
        print(f"Ошибка получения тегов: {e}")
        all_tags = []  # Если таблица тегов ещё не создана

    return templates.TemplateResponse("create_article.html", {
        "request": request,
        "current_user": current_user,
        "tags": all_tags
    })

@app.get("/articles/{article_id}", response_class=HTMLResponse)
async def article_detail_page(
        request: Request,
        article_id: int,
        db: Session = Depends(get_db)
):
    current_user = await get_current_user(request, db=db)

    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        return templates.TemplateResponse("404.html", {
            "request": request,
            "current_user": current_user
        }, status_code=404)

    article.author = db.query(User).filter(User.id == article.author_id).first()
    comments = db.query(Comment).filter(Comment.article_id == article_id).all()

    for comment in comments:
        comment.author = db.query(User).filter(User.id == comment.author_id).first()

    tags = article.tags if hasattr(article, "tags") else []

    likes_count = db.query(Like).filter(Like.article_id == article.id).count()
    is_liked = False
    if  current_user:
        existing_like = db.query(Like).filter(and_(Like.user_id == current_user.id, Like.article_id == article_id)).first()
        is_liked = bool(existing_like)

    return templates.TemplateResponse("article_detail.html", {
        "request": request,
        "current_user": current_user,
        "article": article,
        "comments": comments,
        "tags": tags,
        "likes_count": likes_count,
        "is_liked": is_liked
    })





@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, db: Session = Depends(get_db)):
    current_user = await get_current_user(request, db=db)
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    user_articles = db.query(Article).filter(Article.author_id == current_user.id).all()

    return templates.TemplateResponse("profile.html", {
        "request": request,
        "current_user": current_user,
        "user_articles": user_articles
    })


@app.post("/api/register")
async def register_user(
        request: Request,
        username: str = Form(...),
        email: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):

    db_user = db.query(User).filter(User.username == username).first()
    if db_user:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Имя пользователя уже занято"
        })

    db_user = db.query(User).filter(User.email == email).first()
    if db_user:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Email уже используется"
        })

    hashed_password = User.hash_password(password)
    db_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    access_token = create_access_token(data={"sub": db_user.username})
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(key="access_token", value=access_token, httponly=True)

    return response


@app.post("/api/login")
async def login_user(
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()

    if not user or not user.verify_password(password):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Неверное имя пользователя или пароль"
        })

    access_token = create_access_token(data={"sub": user.username})
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(key="access_token", value=access_token, httponly=True)

    return response


@app.get("/api/logout")
async def logout():
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie(key="access_token")
    return response


@app.post("/api/articles/{article_id}/comments")
async def create_comment_api(
        request: Request,
        article_id: int,
        content: str = Form(...),
        db: Session = Depends(get_db)
):
    current_user = await get_current_user(request, db=db)
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        return RedirectResponse("/articles", status_code=303)

    db_comment = Comment(
        content=content,
        article_id=article_id,
        author_id=current_user.id
    )

    db.add(db_comment)
    db.commit()

    return RedirectResponse(f"/articles/{article_id}", status_code=303)


@app.post("/api/articles/{article_id}/delete")
async def delete_article_api(
        request: Request,
        article_id: int,
        db: Session = Depends(get_db)
):
    current_user = await get_current_user(request, db=db)
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    article = db.query(Article).filter(Article.id == article_id).first()

    if article and article.author_id == current_user.id:
        db.delete(article)
        db.commit()

    return RedirectResponse("/profile", status_code=303)


@app.post("/api/profile/update")
async def update_profile(
        request: Request,
        username: str = Form(...),
        email: str = Form(...),
        full_name: str = Form(None),
        current_password: str = Form(...),
        new_password: Optional[str] = Form(None),
        db: Session = Depends(get_db)
):
    current_user = await get_current_user(request, db=db)
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    if not current_user.verify_password(current_password):
        return templates.TemplateResponse("profile.html", {
            "request": request,
            "current_user": current_user,
            "user_articles": db.query(Article).filter(Article.author_id == current_user.id).all(),
            "error": "Неверный текущий пароль"
        })

    try:
        if username != current_user.username:
            current_user.username = username

        if email != current_user.email:
            current_user.email = email

        current_user.full_name = full_name

        if new_password:
            current_user.hashed_password = User.hash_password(new_password)

        db.commit()

        if username != current_user.username:
            access_token = create_access_token(data={"sub": username})
            response = RedirectResponse("/profile", status_code=303)
            response.set_cookie(key="access_token", value=access_token, httponly=True)
            return response

        return RedirectResponse("/profile?message=Профиль успешно обновлен", status_code=303)

    except IntegrityError as e:
        db.rollback()
        error_msg = "Ошибка уникальности: "
        if "username" in str(e):
            error_msg += "Имя пользователя уже занято"
        elif "email" in str(e):
            error_msg += "Email уже используется"
        else:
            error_msg += "Неизвестная ошибка базы данных"

        return templates.TemplateResponse("profile.html", {
            "request": request,
            "current_user": current_user,
            "user_articles": db.query(Article).filter(Article.author_id == current_user.id).all(),
            "error": error_msg
        })

@app.post("/api/articles/{article_id}/like")
async def like_article(
        request: Request,
        article_id: int,
        db: Session = Depends(get_db)
):
    current_user = await get_current_user(request, db=db)
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    article = db.query(Article).filter(Article.id == article_id).first()

    if not article:
        return RedirectResponse(f"/articles/{article_id}", status_code=303)

    existing_like = db.query(Like).filter(and_(Like.user_id == current_user.id, Like.article_id == article_id)).first()

    if existing_like:
        db.delete(existing_like)
        db.commit()
    else:
        like = Like(user_id=current_user.id, article_id=article_id)
        db.add(like)
        db.commit()
    return RedirectResponse(f"/articles/{article_id}", status_code=303)


@app.get("/api/articles/{article_id}/likes/count")
async def get_article_likes_count(
        article_id: int,
        db: Session = Depends(get_db)
):
    count = db.query(Like).filter(Like.article_id == article_id).count()
    return {"likes_count": count}


@app.get("/articles/{article_id}/edit")
async def edit_article_page(
        request: Request,
        article_id: int,
        db: Session = Depends(get_db)
):
    current_user = await get_current_user(request, db=db)

    if not current_user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")

    article = db.query(Article).filter(Article.id == article_id).first()

    if not article:
        raise HTTPException(status_code=404, detail="Статья не найдена")

    if article.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    all_tags = db.query(Tag).all()

    return templates.TemplateResponse("edit_article.html", {
        "request": request,
        "article": article,
        "all_tags": all_tags,
        "current_user": current_user
    })


@app.post("/articles/{article_id}/edit")
async def edit_article(
        request: Request,
        article_id: int,
        db: Session = Depends(get_db)
):
    current_user = await get_current_user(request, db=db)

    if not current_user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")

    form_data = await request.form()
    title = form_data.get("title")
    content = form_data.get("content")
    tag_names = form_data.getlist("tags")

    if not title or not content:
        raise HTTPException(status_code=400, detail="Заголовок и содержание обязательны")

    article = db.query(Article).filter(Article.id == article_id).first()

    if not article:
        raise HTTPException(status_code=404, detail="Статья не найдена")

    if article.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    article.title = title
    article.content = content
    article.updated_at = datetime.now()

    article.tags.clear()

    for tag_name in tag_names:
        if tag_name.strip():
            tag = db.query(Tag).filter(Tag.name == tag_name.strip()).first()
            if not tag:
                tag = Tag(name=tag_name.strip())
                db.add(tag)
                db.flush()
            article.tags.append(tag)

    db.commit()

    return RedirectResponse(f"/articles/{article.id}", status_code=303)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)