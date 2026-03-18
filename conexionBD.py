from fastapi import Depends, FastAPI, Request, HTTPException, status, Form
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from cassandra.cluster import Cluster
from cassandra.query import dict_factory
import uvicorn 
import uuid
from datetime import date
from decimal import Decimal
import logging
import admin_auth


