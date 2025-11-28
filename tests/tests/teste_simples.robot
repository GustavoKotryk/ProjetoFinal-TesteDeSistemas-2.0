*** Settings ***
Library    SeleniumLibrary

*** Test Cases ***
Teste Carregamento Página Inicial
    Open Browser    https://projetofinal-testedesistemas-2-0.onrender.com    chrome
    Maximize Browser Window
    Page Should Contain    Conectando ONGs e Voluntários
    Page Should Contain Element    //a[contains(text(), 'Entrar')]
    Close Browser

Teste Navegação Básica
    Open Browser    https://projetofinal-testedesistemas-2-0.onrender.com    chrome
    Maximize Browser Window

    # Testa link de cadastro
    Click Element    //a[contains(text(), 'Cadastrar')]
    Wait Until Page Contains    Cadastro de Voluntário    timeout=10s

    # Volta para home
    Click Element    //a[contains(text(), 'Rede Voluntariado')]
    Wait Until Page Contains    Conectando ONGs e Voluntários    timeout=10s

    Close Browser