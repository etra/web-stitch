"""Image upload and gallery routes"""
from flask import render_template, request, redirect, url_for, flash, session, jsonify, send_file

from stitch.blueprints.images import bp
from stitch.blueprints.auth.routes import login_required
from stitch.services.image_service import ImageService
from stitch.services.color_matcher import ColorMatcher
from stitch.services.project_service import ProjectService


@bp.route('/', methods=['GET', 'POST'])
@login_required
def gallery():
    """
    Image gallery page with upload.

    GET: Display gallery
    POST: Upload new image
    """
    user_id = session.get('user_id')

    if request.method == 'POST':
        if 'image' not in request.files:
            flash('No file selected.', 'danger')
            return redirect(url_for('images.gallery'))

        file = request.files['image']

        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(url_for('images.gallery'))

        try:
            ImageService.upload_image(user_id, file)
            flash('Image uploaded successfully!', 'success')
            return redirect(url_for('images.gallery'))

        except ValueError as e:
            flash(str(e), 'danger')
            return redirect(url_for('images.gallery'))

        except Exception:
            flash('An error occurred while uploading the image.', 'danger')
            return redirect(url_for('images.gallery'))

    # GET request - show gallery
    images = ImageService.get_user_images(user_id)

    for image in images:
        image['processed_versions'] = ImageService.get_processed_versions(
            user_id,
            image['filename']
        )

    return render_template('images/gallery.html', images=images)


@bp.route('/delete/<filename>', methods=['POST'])
@login_required
def delete(filename):
    """Delete an image."""
    user_id = session.get('user_id')

    try:
        if ImageService.delete_image(user_id, filename):
            flash('Image deleted successfully.', 'success')
        else:
            flash('Image not found.', 'warning')
    except Exception:
        flash('An error occurred while deleting the image.', 'danger')

    return redirect(url_for('images.gallery'))


@bp.route('/thumbnail/<filename>')
@login_required
def thumbnail(filename):
    """Serve thumbnail image."""
    user_id = session.get('user_id')
    thumb_path = ImageService.get_thumbnail_path(user_id, filename)

    if thumb_path:
        return send_file(thumb_path, mimetype='image/jpeg')
    else:
        return '', 404


@bp.route('/process-ajax', methods=['POST'])
@login_required
def process_ajax():
    """AJAX endpoint for real-time image processing preview."""
    user_id = session.get('user_id')

    try:
        data = request.get_json()
        filename = data.get('filename')
        target_width = int(data.get('width', 100))
        target_height = int(data.get('height', 100))
        num_colors = int(data.get('colors', 20))

        # Validation
        if target_width < 10 or target_width > 500:
            return jsonify({'error': 'Width must be between 10 and 500'}), 400
        if target_height < 10 or target_height > 500:
            return jsonify({'error': 'Height must be between 10 and 500'}), 400
        if num_colors < 2 or num_colors > 100:
            return jsonify({'error': 'Colors must be between 2 and 100'}), 400

        result = ImageService.generate_preview(
            user_id, filename, target_width, target_height, num_colors
        )

        return jsonify({
            'success': True,
            **result
        })

    except FileNotFoundError:
        return jsonify({'error': 'Image not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/prepare/<filename>', methods=['GET', 'POST'])
@login_required
def prepare(filename):
    """Prepare image for cross-stitch pattern."""
    user_id = session.get('user_id')

    if request.method == 'POST':
        try:
            target_width = int(request.form.get('width', 100))
            target_height = int(request.form.get('height', 100))
            num_colors = int(request.form.get('colors', 20))

            result = ImageService.process_pattern_image(
                user_id, filename, target_width, target_height, num_colors
            )

            # Store in session for next steps
            session['processed_image'] = {
                'filename': result['processed_filename'],
                'original_filename': filename,
                'width': target_width,
                'height': target_height,
                'palette': result['used_palette'],
                'num_colors': len(result['used_palette']),
                'processing_params': {
                    'width': target_width,
                    'height': target_height,
                    'colors': num_colors
                }
            }

            flash('Settings confirmed! Proceeding to DMC color matching.', 'success')
            return redirect(url_for('images.match_colors'))

        except FileNotFoundError:
            flash('Image not found.', 'danger')
            return redirect(url_for('images.gallery'))
        except Exception as e:
            flash(f'Error processing image: {str(e)}', 'danger')
            return redirect(url_for('images.prepare', filename=filename))

    # GET request - show processing form
    try:
        dimensions = ImageService.get_image_dimensions(user_id, filename)
        return render_template('images/prepare.html',
                               filename=filename,
                               original_width=dimensions['width'],
                               original_height=dimensions['height'])
    except FileNotFoundError:
        flash('Image not found.', 'danger')
        return redirect(url_for('images.gallery'))
    except ValueError as e:
        flash(f'Error loading image: {str(e)}', 'danger')
        return redirect(url_for('images.gallery'))


@bp.route('/preview')
@login_required
def preview_processed():
    """Preview processed image before creating project."""
    processed_data = session.get('processed_image')

    if not processed_data:
        flash('No processed image found. Please process an image first.', 'warning')
        return redirect(url_for('images.gallery'))

    return render_template('images/preview.html', processed_data=processed_data)


@bp.route('/match-colors', methods=['GET', 'POST'])
@login_required
def match_colors():
    """Match quantized colors to DMC palette."""
    processed_data = session.get('processed_image')

    if not processed_data:
        flash('No processed image found. Please process an image first.', 'warning')
        return redirect(url_for('images.gallery'))

    if request.method == 'POST':
        selected_indices = request.form.getlist('selected')
        use_dmc_flags = request.form.getlist('use_dmc')

        matched_colors = session.get('matched_colors', [])
        ColorMatcher.update_selection(matched_colors, selected_indices, use_dmc_flags)

        final_palette = ColorMatcher.create_dmc_mapped_palette(matched_colors)

        processed_data['palette'] = final_palette
        processed_data['num_colors'] = len(final_palette)
        session['processed_image'] = processed_data
        session.pop('matched_colors', None)

        flash(f'Colors matched! Using {len(final_palette)} colors for your project.', 'success')
        return redirect(url_for('images.create_project_from_image'))

    # GET request - perform color matching
    try:
        matched_colors = ColorMatcher.match_palette_to_dmc(
            processed_data['palette'],
            palette_name='dmc'
        )
        session['matched_colors'] = matched_colors

        return render_template('images/match_colors.html',
                               processed_data=processed_data,
                               matched_colors=matched_colors)
    except Exception as e:
        flash(f'Error matching colors: {str(e)}', 'danger')
        return redirect(url_for('images.prepare',
                                filename=processed_data.get('original_filename', '')))


@bp.route('/create-from-processed/<filename>')
@login_required
def create_from_processed(filename):
    """Load a saved processed image and go directly to project creation."""
    user_id = session.get('user_id')

    try:
        metadata = ImageService.load_processed_metadata(user_id, filename)
        session['processed_image'] = metadata

        flash(f'Loaded processed version: {metadata["width"]}×{metadata["height"]}, '
              f'{metadata["num_colors"]} colors', 'success')
        return redirect(url_for('images.create_project_from_image'))

    except FileNotFoundError:
        flash('Processed image not found.', 'danger')
        return redirect(url_for('images.gallery'))
    except Exception as e:
        flash(f'Error loading processed image: {str(e)}', 'danger')
        return redirect(url_for('images.gallery'))


@bp.route('/create-project', methods=['GET', 'POST'])
@login_required
def create_project_from_image():
    """Create project from processed image."""
    user_id = session.get('user_id')
    processed_data = session.get('processed_image')

    if not processed_data:
        flash('No processed image found. Please process an image first.', 'warning')
        return redirect(url_for('images.gallery'))

    if request.method == 'POST':
        project_name = request.form.get('name', '').strip()

        if not project_name:
            flash('Project name is required.', 'danger')
            return render_template('images/create_project.html', processed_data=processed_data)

        try:
            upload_dir = ImageService.get_upload_dir(user_id)
            processed_image_path = str(upload_dir / 'processed' / processed_data['filename'])
            original_image_path = str(upload_dir / 'originals' / processed_data['original_filename'])

            project = ProjectService.create_project_from_image(
                user_id=user_id,
                name=project_name,
                processed_data=processed_data,
                processed_image_path=processed_image_path,
                original_image_path=original_image_path
            )

            # Clear session data
            session.pop('processed_image', None)
            session.pop('matched_colors', None)

            flash(f'Project "{project_name}" created! Image: {project.image_cells_count} stitches, '
                  f'Edges: {project.edge_cells_count} stitches, {project.num_colors} colors. '
                  f'You can create more projects from this processed image.', 'success')
            return redirect(url_for('editor.canvas', project_id=project.id))

        except FileNotFoundError as e:
            flash(str(e), 'danger')
            return render_template('images/create_project.html', processed_data=processed_data)
        except Exception as e:
            flash(f'Error creating project: {str(e)}', 'danger')
            return render_template('images/create_project.html', processed_data=processed_data)

    # GET request - show project creation form
    return render_template('images/create_project.html', processed_data=processed_data)
