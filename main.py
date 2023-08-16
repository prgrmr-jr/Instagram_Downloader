import sys
import urllib
import zipfile
from datetime import datetime
import requests
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QFileDialog, QMessageBox
from PyQt5.uic import loadUi
from instaloader import instaloader


class InstagramDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.download: str = 'type'

        try:
            loadUi("./assets/ui/igdownloader.ui", self)
            self.setWindowTitle("Instagram Downloader")
            self.setWindowIcon(QIcon("./assets/images/logo_ig.png"))
            self.btnSearch.clicked.connect(self.search_thumbnails)
            self.btnDownload.setVisible(False)
            self.btnDownload.clicked.connect(self.download_instagram_by_link)

        except Exception as e:
            print(f"Error loading UI file: {str(e)}")

    def download_instagram_by_link(self):
        self.clear_thumbnails()
        post_url = self.inputLink.text()
        insta = instaloader.Instaloader()
        post = instaloader.Post.from_shortcode(insta.context, post_url.split("/")[-2])

        # Check if the post is a video
        if post.is_video:
            thumbnail_url = post.url
            # Get the video URL
            video_url = post.video_url
            # Get the username of the author of the post
            username: str = post.owner_username
            # Create the filename for the video
            filename = username + '_instagram_video.mp4'
            # Ask the user to select a directory to save the video
            save_location, _ = QFileDialog.getSaveFileName(self, 'Save Audio', filename,
                                                           'Audio Files (*.mp4)')
            if save_location:
                # Download the video to user specified location
                urllib.request.urlretrieve(video_url, save_location + '.mp4')
                # Display successful message
                QMessageBox.information(self, 'Download Finished', 'Instagram video has been successfully downloaded.')
            else:
                QMessageBox.warning(self, 'Download Cancelled', 'The download has been cancelled.')

        # Check if the post is a sidecar or carousel post
        elif post.typename == 'GraphSidecar':

            sidecar_nodes = post.get_sidecar_nodes()

            # Get the username of the author of the post

            username = post.owner_username

            # Get the current date in the format DD-MM-YYYY

            date_str = datetime.now().strftime('%d-%m-%Y')

            # Create the filename for the zip file

            filename = f'{username}_{date_str}.zip'

            # Ask the user to select a directory to save the zip file

            save_location, _ = QFileDialog.getSaveFileName(self, 'Save Images and Videos', filename,
                                                           'Zip Files (*.zip)')

            if save_location:

                # Create a new zip file

                with zipfile.ZipFile(save_location, 'w') as myzip:

                    for idx, node in enumerate(sidecar_nodes, start=1):

                        if node.is_video:

                            video_url = node.video_url

                            video_filename = f'instagram_video_{idx}.mp4'

                            # Download the video data

                            response = requests.get(video_url)

                            # Write the video data to the zip file

                            myzip.writestr(video_filename, response.content)

                        else:

                            image_url = node.display_url

                            image_filename = f'instagram_image_{idx}.png'

                            # Download the image data

                            response = requests.get(image_url)

                            # Write the image data to the zip file

                            myzip.writestr(image_filename, response.content)

                # Display successful message

                QMessageBox.information(self, 'Download Finished',
                                        'Instagram images and videos have been successfully downloaded.')

            else:
                QMessageBox.warning(self, 'Download Cancelled', 'The download has been cancelled.')

        # Check if the post is an image
        else:
            thumbnail_url = post.url
            username: str = post.owner_username
            filename = username + '_instagram_image.png'
            save_location, _ = QFileDialog.getSaveFileName(self, 'Save Image', filename, 'Image Files (*.png)')
            if save_location:
                urllib.request.urlretrieve(thumbnail_url, save_location + '.png')
                QMessageBox.information(self, 'Download Finished',
                                        'Instagram image has been successfully downloaded.')
            else:
                QMessageBox.warning(self, 'Download Cancelled', 'The download has been cancelled.')

        self.clear_thumbnails()
        self.inputLink.setText('')
        self.btnDownload.setVisible(False)

    def search_thumbnails(self):
        self.clear_thumbnails()
        post_url = self.inputLink.text()
        self.btnDownload.setVisible(True)
        insta = instaloader.Instaloader()
        post = instaloader.Post.from_shortcode(insta.context, post_url.split("/")[-2])

        if post.is_video:
            thumbnail_url = post.url
            self.download = 'video'
            self.display_thumbnails(thumbnail_url)
        elif post.typename == 'GraphSidecar':
            images_and_videos = []
            for node in post.get_sidecar_nodes():
                images_and_videos.append(node.display_url)
            self.download = 'image'
            self.display_thumbnails(images_and_videos)
        else:
            thumbnail_url = post.url
            self.download = 'image'
            self.display_thumbnails(thumbnail_url)

    def display_thumbnails(self, urls):
        if isinstance(urls, str):  # Handle single URL
            response = requests.get(urls)
            pixmap = QPixmap()
            pixmap.loadFromData(response.content)

            label = QLabel()
            label.setStyleSheet('border: 1px solid #EEEEEE;')
            label.setPixmap(pixmap.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            label.setScaledContents(True)
            self.thumbnail_layout.addWidget(label, 0, 0, alignment=Qt.AlignCenter)

        elif isinstance(urls, list):  # Handle list of URLs
            row = 0
            col = 0

            for idx, url in enumerate(urls, start=1):
                response = requests.get(url)
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)

                label = QLabel()
                label.setStyleSheet('border: 1px solid #EEEEEE;')
                if len(urls) <= 3:
                    label.setPixmap(pixmap.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    self.thumbnail_layout.addWidget(label, row, col, alignment=Qt.AlignCenter)
                else:
                    label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    self.thumbnail_layout.addWidget(label, row, col)

                col += 1
                if col == 5:
                    col = 0
                    row += 1

    def clear_thumbnails(self):
        # Remove all widgets from the layout
        while self.thumbnail_layout.count():
            item = self.thumbnail_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = InstagramDownloader()
    window.show()
    sys.exit(app.exec_())
