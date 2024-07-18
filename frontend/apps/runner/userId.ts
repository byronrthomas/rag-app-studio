import { v4 as uuidv4 } from 'uuid';
import Cookies from 'js-cookie';

export function getUserId() {
    const cookieName = 'user_id';
    let userId = Cookies.get(cookieName);

    if (!userId) {
        userId = uuidv4();
        Cookies.set(cookieName, userId, { expires: 365 * 10 }); // Store the cookie for 10 years

    }

    return userId;
}