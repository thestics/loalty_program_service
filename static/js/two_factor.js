function initTwoFactor (el, secret_el, user_email, size) {
    el.text('');
    el.qrcode({
        width: size,
        height: size,
        text: encodeURI('otpauth://totp/' + document.domain + ':' + user_email +
              '?secret=' + secret_el.val() + '&issuer=' + document.domain)
    });
}
