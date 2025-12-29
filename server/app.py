#!/usr/bin/env python3

from flask import Flask, jsonify, request, session, make_response
from flask_migrate import Migrate
from flask_restful import Api, Resource
from models import db, User, Article

app = Flask(__name__)
app.secret_key = b'Y\xf1Xz\x00\xad|eQ\x80t \xca\x1a\x10K'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

db.init_app(app)
migrate = Migrate(app, db)
api = Api(app)

with app.app_context():

    if not User.query.first():
        user = User(username="testuser")
        db.session.add(user)
        db.session.commit()
    else:
        user = User.query.first()

    if not Article.query.filter_by(is_member_only=True).first():
        article = Article(
            author="Member Author",
            title="Secret Article",
            content="Members Only Content",
            preview="Members Only Preview",
            minutes_to_read=2,
            is_member_only=True,
            user_id=user.id
        )
        db.session.add(article)
        db.session.commit()

class ClearSession(Resource):
    def delete(self):
        session.clear()
        return {}, 204

class IndexArticle(Resource):
    def get(self):
        articles = [article.to_dict() for article in Article.query.all()]
        return make_response(jsonify(articles), 200)

class ShowArticle(Resource):
    def get(self, id):
        article = db.session.get(Article, id)
        if not article:
            return {'error': 'Article not found'}, 404

        if not session.get('user_id'):
            session['page_views'] = session.get('page_views', 0) + 1
            if session['page_views'] > 3:
                return {'message': 'Maximum pageview limit reached'}, 401

        return make_response(jsonify(article.to_dict()), 200)

class Login(Resource):
    def post(self):
        username = request.get_json().get('username')
        user = User.query.filter_by(username=username).first()
        if user:
            session['user_id'] = user.id
            return user.to_dict(), 200
        return {}, 401

class Logout(Resource):
    def delete(self):
        session.clear()
        return {}, 204

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            if user:
                return user.to_dict(), 200
        return {}, 401

class MemberOnlyIndex(Resource):
    def get(self):
        if not session.get('user_id'):
            return {'error': 'You must be logged in to access member content'}, 401

        articles = [a.to_dict() for a in Article.query.filter_by(is_member_only=True).all()]
        return make_response(jsonify(articles), 200)

class MemberOnlyArticle(Resource):
    def get(self, id):
        if not session.get('user_id'):
            return {'error': 'You must be logged in to access member content'}, 401


        article = db.session.get(Article, id)
        if not article:
            return {'error': 'Article not found'}, 404


        if not article.is_member_only:
            return {'error': 'Member-only article not found'}, 404

        return make_response(jsonify(article.to_dict()), 200)

api.add_resource(ClearSession, '/clear')
api.add_resource(IndexArticle, '/articles')
api.add_resource(ShowArticle, '/articles/<int:id>')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(CheckSession, '/check_session')
api.add_resource(MemberOnlyIndex, '/members_only_articles')
api.add_resource(MemberOnlyArticle, '/members_only_articles/<int:id>')

if __name__ == '__main__':
    app.run(port=5555, debug=True)
