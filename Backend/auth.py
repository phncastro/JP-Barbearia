import os

from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from Backend.database import SessionLocal
from Backend.models import Usuario, Identidade

load_dotenv()

router = APIRouter()

oauth = OAuth()

oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile"
    }
)

@router.get("/auth/google")
async def google_login(request: Request):
    redirect_uri = request.url_for("google_callback")

    print("REDIRECT URI:", redirect_uri)
    
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/auth/google/callback", name="google_callback")
async def google_callback(request: Request):
    # 1. Troca o código de autorização pelas informações do Google
    token = await oauth.google.authorize_access_token(request)

    userinfo = token.get("userinfo")

    if not userinfo:
        userinfo = await oauth.google.userinfo(token=token)

    if not userinfo:
        raise HTTPException(
            status_code=401,
            detail="Não foi possível obter os dados do usuário."
        )

    # 2. Valida os dados essenciais da identidade
    google_sub = userinfo.get("sub") if userinfo else None
    email = userinfo.get("email") if userinfo else None
    email_verified = userinfo.get("email_verified") if userinfo else False

    if not google_sub or not email or not email_verified:
        raise HTTPException(
            status_code=401,
            detail="Não foi possível validar a identidade e o e-mail do Google.",
        )

    # 3. Abre uma sessão com o banco de dados
    with SessionLocal() as db:

        # Procura a identidade Google pelo identificador único
        identidade = db.scalar(
            select(Identidade).where(
                Identidade.provedor == "google",
                Identidade.provider_user_id == google_sub,
            )
        )

        if identidade:
            # A pessoa já possui cadastro
            usuario = identidade.usuario

        else:
            # Verifica se o e-mail já pertence a outra conta
            usuario_existente = db.scalar(
                select(Usuario).where(Usuario.email == email)
            )

            if usuario_existente:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Já existe uma conta com este e-mail. "
                        "Entre pelo método já vinculado para associar o Google."
                    ),
                )

            # Cria o usuário interno da JP-Barbearia
            usuario = Usuario(
                nome=userinfo.get("name") or email.split("@")[0],
                email=email,
                foto_url=userinfo.get("picture"),
            )

            # Associa a identidade externa ao usuário
            identidade = Identidade(
                provedor="google",
                provider_user_id=google_sub,
            )

            usuario.identidades.append(identidade)
            db.add(usuario)

            try:
                db.commit()
                db.refresh(usuario)

            except IntegrityError:
                db.rollback()
                raise HTTPException(
                    status_code=409,
                    detail="Não foi possível concluir o cadastro. Tente entrar novamente.",
                )

        # 4. Registra o usuário na sessão da aplicação
        request.session["user_id"] = usuario.id

        # Resposta temporária para testar o funcionamento
        return {
            "message": "Login realizado com sucesso!",
            "user": {
                "id": usuario.id,
                "nome": usuario.nome,
                "email": usuario.email,
                "foto_url": usuario.foto_url,
            },
        }