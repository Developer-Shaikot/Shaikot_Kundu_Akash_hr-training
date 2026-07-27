user = env['res.users'].search([('login', '=', 'admin')])  # type: ignore
if user:
    user.write({'login': 'saikatkundu43@gmail.com', 'password': '123456'})
    env.cr.commit()  # type: ignore
