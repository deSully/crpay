location /static/ {
    alias /app/staticfiles/;
    access_log off;
    expires 30d;
}

location /media/ {
    alias /app/media/;
    access_log off;
    expires 30d;
}
