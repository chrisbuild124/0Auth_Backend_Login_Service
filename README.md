# CS 361 Team 16 - Microservice 3 (Small Pool) & 4-5 (Large Pool)

### Overview
- Three microservices in repository:
    - Backend VerifyJWT *(in pogress - large pool)*
        - Verifies Authenticity - Verify JWT tokens
    - Backend Redis *(in pogress - large pool)*
        - JWT Cache Logout - Cache JWT tokens
    - Backend Auth0 (Small Pool)
        - Proves Identity - authenticate user to database
        - Creates Authenticity - Create JWT tokens
        - Verifies Authenticity - Verify JWT tokens *(for now)*

# NOTES
### Backend VerifyJWT Microservice - Large Pool
### Backend Redis Microservice - Large Pool
### Backend Auth0 Microservice - Small Pool

How to request data from the microservice:
- d
Example call for requesting data:
- d
How to receive data from the microservice:
- d
Example call for receiving data:
- d
UML sequence diagram:
- d
UML Diagram Description:
Frontend:
- Type URL for homepage to login (Web)
    - Homepage is redirected to `/login` (Web)
        - `/login` redirects to backend `/login` (Web)
- Click link redirects to backend /login (CLI)

Backend `/login` (CLI or Web):
- Finds the application system type the user is coming from (`CLI` = CLI, `Flask` = Web)
- Creates a URL and the user is redirected to Auth0's login page for the specific app system type and asks the user to login into Auth0's identity database
    - Each database holds its own login records
    - User can login or create an account
- User is logged in and sent to the backend's database's `/callback`

Backend `/callback` (CLI or Web):
- Backend server receives auth code from auth0 via URL
    - The Auth code is a 1 time usable code to establish an access token with Auth0
- Auth code is exchanged for access token from Auth0
- The access token is used to get user information
    - Access token is then lost in code (for good reason) after user info is retrieved
- Establishes a JWT: 
    - Method 1 (used): Private/Public JWT
        - Private key is used to encode JWT
        - User info is stored into JWT
    - Method 2 (not used): Shared JWT method 
        - Not appliceable here since it is talking from frontend to backend, and not two backend systems
- To return to frontend:
    - Returns to the frontend URL's homepage for the user's login with JWT inside the cookie (Web)
    - Returns to a browser with the JWT private/public token (CLI)

Frontend:
- Retrieves cookie from webbrowser and renders homepage (Web)
- Enters JWT in CLI and keeps saved in session (CLI)
- Each new page requiring login verification, each system (CLI or Web) calls backend `/verify-user`

Backend `/verify-user` (CLI or Web):
- Checks if JWT exists in JSON body
    - Uses `public.pem` key to verify JWT
- Verifies and sends back user info in JSON body
    - Frontend could do this but is done on the backend

Logout:
- Save over old cookie jwt as a new cookie, with it expiring immediately (Web)
- Remove saved JWT (CLI)
- Directs user to login page (CLI & Web)

# Additional Notes
- Additional cookie, JWT, and Flask documentation can be found on READme at [Calorie Tracker READme](https://github.com/chrisbuild124/Calorie-Tracker/blob/main/README.md)
- Additional CLI docuemntation can be found at [CLI Repository](https://github.com/quetzlcoatlus/project-repository)

### Group Members
- Alexander Lane
- Gregory Preiss
- Christopher Sexton

### Repo-Contributors 
- Alexander Lane
- Christopher Sexton

### Repo-Users
- Alexander Lane
- Christopher Sexton