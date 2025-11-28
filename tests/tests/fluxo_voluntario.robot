*** Settings ***
Library    SeleniumLibrary
Library    DateTime
Suite Setup    Abrir Navegador
Suite Teardown    Fechar Navegador

*** Variables ***
${URL}    https://projetofinal-testedesistemas-2-0.onrender.com
${BROWSER}    chrome

*** Test Cases ***
Teste Carregamento Página Inicial
    [Documentation]    Testa se a página inicial carrega corretamente
    Page Should Contain    Conectando ONGs e Voluntários
    Page Should Contain Element    xpath=//a[contains(., 'Entrar')]

Teste Navegação Para Cadastro
    [Documentation]    Testa a navegação para página de cadastro
    # Clica no dropdown de cadastro
    Click Element    xpath=//button[contains(., 'Cadastrar')]
    # Clica em "Como Voluntário"
    Click Element    xpath=//a[contains(., 'Como Voluntário')]
    Wait Until Page Contains    Cadastro de Voluntário    timeout=10
    Page Should Contain    Cadastro de Voluntário

Teste Cadastro Voluntário Simples
    [Documentation]    Testa o cadastro básico de voluntário
    Go To    ${URL}/cadastro/usuario

    # Gera email único
    ${timestamp}    Get Current Date    result_format=%H%M%S
    ${email}    Set Variable    robot${timestamp}@teste.com

    # Preenche formulário mínimo
    Input Text    id=nome    Teste Robot
    Input Text    id=email    ${email}
    Input Text    id=senha    123456
    Input Text    id=cidade    São Paulo

    Click Button    xpath=//button[contains(., 'Cadastrar como Voluntário')]

    # Verifica se foi para login
    Wait Until Page Contains    Entrar    timeout=10
    Page Should Contain    Entrar

*** Keywords ***
Abrir Navegador
    Open Browser    ${URL}    ${BROWSER}
    Maximize Browser Window
    Set Selenium Implicit Wait    10 seconds

Fechar Navegador
    Close Browser