from flask import Flask, render_template, request, redirect
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, URL
from flask_sqlalchemy import SQLAlchemy
import ast

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)


# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///joblistings.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Job listing TABLE Configuration
class JobListing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    company = db.Column(db.String, nullable=False)
    job_description = db.Column(db.String, nullable=False)
    post_url = db.Column(db.String, nullable=False)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


# Archive TABLE configuration
class Archive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    company = db.Column(db.String, nullable=False)
    job_description = db.Column(db.String, nullable=False)
    post_url = db.Column(db.String, nullable=False)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

db.create_all()


# Job posting form fields
class JobForm(FlaskForm):
    title = StringField(label="Job title", validators=[DataRequired()])
    company = StringField(label="Company", validators=[DataRequired()])
    job_description = TextAreaField(label="Job description", validators=[DataRequired()])
    post_url = StringField(label="Post URL", validators=[DataRequired(), URL()])
    search_terms = StringField(label="Enter search terms separated by a comma and space.", validators=[DataRequired()])
    submit = SubmitField(label='Submit')


def read_listing(listing):
    search_terms = listing["search_terms"].split(", ")
    found_terms = [term for term in search_terms if term.lower() in listing["job_description"].lower()]
    return found_terms


@app.route("/add", methods=["GET", "POST"])
def add_job_listing():
    form = JobForm()
    if form.validate_on_submit():
        listing = {"title": form.title.data,
                   "company": form.company.data,
                   "job_description": form.job_description.data,
                   "post_url": form.post_url.data,
                   "search_terms": form.search_terms.data}
        found_terms = read_listing(listing)
        if len(found_terms) > 0:
            return render_template("results.html", found_terms=found_terms, listing=listing)
        else:
            return "<h2>No search terms found</h2>"
    return render_template("add.html", form=form)


@app.route("/add_to_db")
def add_to_db():
    listing = request.args.get("listing")
    listing_dict = ast.literal_eval(listing)
    listing_to_add = JobListing(company=listing_dict["company"],
                                title=listing_dict["title"],
                                job_description=listing_dict["job_description"],
                                post_url=listing_dict["post_url"])
    db.session.add(listing_to_add)
    db.session.commit()
    return redirect("/view_jobs")


@app.route("/view_jobs")
def view_jobs():
    all_listings = db.session.query(JobListing).all()
    all_listings_as_dicts = [listing.to_dict() for listing in all_listings]
    return render_template("jobs.html", all_listings=all_listings_as_dicts)


@app.route("/archive/<job_id>")
def archive(job_id):
    job_to_archive = JobListing.query.get(job_id)
    listing_dict = job_to_archive.to_dict()
    listing_to_add = Archive(company=listing_dict["company"],
                             title=listing_dict["title"],
                             job_description=listing_dict["job_description"],
                             post_url=listing_dict["post_url"])
    db.session.add(listing_to_add)
    db.session.commit()
    delete(job_id)
    return redirect("/view_archive")


@app.route("/un_archive/<job_id>")
def un_archive(job_id):
    to_un_archive = Archive.query.get(job_id)
    listing_dict = to_un_archive.to_dict()
    listing_to_add = JobListing(company=listing_dict["company"],
                                title=listing_dict["title"],
                                job_description=listing_dict["job_description"],
                                post_url=listing_dict["post_url"])
    db.session.add(listing_to_add)
    db.session.commit()
    delete_from_archive(job_id)
    return redirect("/view_jobs")


@app.route("/view_archive")
def view_archive():
    all_listings = db.session.query(Archive).all()
    all_listings_as_dicts = [listing.to_dict() for listing in all_listings]
    return render_template("archive.html", all_listings=all_listings_as_dicts)


@app.route("/delete/<job_id>")
def delete(job_id):
    job_to_delete = JobListing.query.get(job_id)
    db.session.delete(job_to_delete)
    db.session.commit()
    return redirect("/view_jobs")


def delete_from_archive(job_id):
    job_to_delete = Archive.query.get(job_id)
    db.session.delete(job_to_delete)
    db.session.commit()
    return redirect("/view_jobs")


@app.route("/confirm_delete")
def confirm_delete():
    job = ast.literal_eval(request.args.get("job"))
    return render_template("confirm-delete.html", listing=job)


if __name__ == "__main__":
    app.run(debug=True)